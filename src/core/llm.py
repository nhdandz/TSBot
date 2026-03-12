"""vLLM LLM service wrapper cho TSBot.

vLLM chạy trên máy A100, expose OpenAI-compatible API.
Dùng ChatOpenAI từ langchain-openai để giao tiếp.
"""

import logging
import time
from typing import Any, AsyncGenerator, Literal, Optional

import httpx
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings

logger = logging.getLogger(__name__)


class ServiceUnavailableError(Exception):
    """vLLM server không khả dụng (circuit breaker open)."""


class CircuitBreaker:
    """Circuit breaker cho vLLM requests."""

    FAILURE_THRESHOLD = 5
    RECOVERY_TIMEOUT = 60  # seconds

    def __init__(self):
        self.state: Literal["closed", "open", "half_open"] = "closed"
        self.failure_count: int = 0
        self.last_failure_time: float = 0.0

    def can_attempt(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure_time > self.RECOVERY_TIMEOUT:
                self.state = "half_open"
                logger.info("Circuit breaker → half_open (trying recovery)")
                return True
            return False
        return True  # half_open: cho phép 1 thử

    def record_success(self):
        if self.state != "closed":
            logger.info(f"Circuit breaker → closed (recovered from {self.state})")
        self.state = "closed"
        self.failure_count = 0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.FAILURE_THRESHOLD:
            if self.state != "open":
                logger.error(f"Circuit breaker → open ({self.failure_count} failures)")
            self.state = "open"
        elif self.state == "half_open":
            self.state = "open"
            logger.warning("Circuit breaker → open (half_open attempt failed)")


class LLMService:
    """vLLM service wrapper với OpenAI-compatible API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        main_model: Optional[str] = None,
        grader_model: Optional[str] = None,
    ):
        self.base_url = base_url or settings.vllm_base_url
        self.main_model = main_model or settings.vllm_main_model
        self.grader_model = grader_model or settings.vllm_grader_model

        self._main_llm: Optional[ChatOpenAI] = None
        self._grader_llm: Optional[ChatOpenAI] = None
        self._circuit_breaker = CircuitBreaker()

    def _make_llm(self, model: str, temperature: float, top_p: Optional[float] = None) -> ChatOpenAI:
        """Tạo ChatOpenAI instance trỏ vào vLLM server."""
        kwargs: dict[str, Any] = {
            "base_url": self.base_url,
            "api_key": settings.vllm_api_key,
            "model": model,
            "temperature": temperature
        }
        if top_p is not None:
            kwargs["top_p"] = top_p
        return ChatOpenAI(**kwargs)

    @property
    def main_llm(self) -> ChatOpenAI:
        """LLM chính cho generation tasks."""
        if self._main_llm is None:
            self._main_llm = self._make_llm(
                model=self.main_model,
                temperature=settings.vllm_main_temperature,
                top_p=settings.vllm_main_top_p,
            )
        return self._main_llm

    @property
    def grader_llm(self) -> ChatOpenAI:
        """LLM nhỏ hơn cho grading/evaluation tasks."""
        if self._grader_llm is None:
            self._grader_llm = self._make_llm(
                model=self.grader_model,
                temperature=settings.vllm_grader_temperature,
            )
        return self._grader_llm

    def get_llm(
        self,
        model: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> ChatOpenAI:
        """Tạo custom LLM instance."""
        return self._make_llm(
            model=model or self.main_model,
            temperature=temperature,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_grader: bool = False,
        **kwargs: Any,
    ) -> str:
        """Gọi LLM và trả về text response."""
        import re

        if not self._circuit_breaker.can_attempt():
            raise ServiceUnavailableError("vLLM không khả dụng (circuit breaker open)")

        llm = self.grader_llm if use_grader else self.main_llm

        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("human", prompt))

        try:
            response = await llm.ainvoke(messages, **kwargs)
            self._circuit_breaker.record_success()
        except Exception as e:
            self._circuit_breaker.record_failure()
            raise

        content = response.content

        # Loại bỏ thinking tags (qwen3, deepseek-r1 và các reasoning models)
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r"<thinking>.*?</thinking>", "", content, flags=re.DOTALL | re.IGNORECASE)

        return content.strip()

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_grader: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream generate responses từ LLM."""
        if not self._circuit_breaker.can_attempt():
            raise ServiceUnavailableError("vLLM không khả dụng (circuit breaker open)")

        llm = self.grader_llm if use_grader else self.main_llm

        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("human", prompt))

        first_token = True
        buffer = ""
        in_think = False

        try:
            async for chunk in llm.astream(messages, **kwargs):
                if not (hasattr(chunk, "content") and chunk.content):
                    continue

                if first_token:
                    self._circuit_breaker.record_success()
                    first_token = False

                buffer += chunk.content

                # Lọc <think>...</think> tags (reasoning models: qwen3, deepseek-r1)
                while True:
                    if in_think:
                        end = buffer.find("</think>")
                        if end == -1:
                            end = buffer.find("</thinking>")
                            tag_len = len("</thinking>")
                        else:
                            tag_len = len("</think>")

                        if end != -1:
                            buffer = buffer[end + tag_len:]
                            in_think = False
                        else:
                            buffer = ""  # discard — vẫn trong think block
                            break
                    else:
                        start = buffer.find("<think>")
                        if start == -1:
                            start = buffer.find("<thinking>")
                        if start != -1:
                            # Yield phần trước think tag
                            if start > 0:
                                yield buffer[:start]
                            buffer = buffer[start:]
                            in_think = True
                        else:
                            # Không có think tag — yield an toàn trừ tail có thể là đầu tag
                            safe = max(0, len(buffer) - 12)  # len("<thinking>") + 2
                            if safe > 0:
                                yield buffer[:safe]
                                buffer = buffer[safe:]
                            break

            # Flush phần còn lại sau khi stream kết thúc
            if buffer and not in_think:
                yield buffer

        except Exception as e:
            self._circuit_breaker.record_failure()
            raise

    async def generate_with_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_grader: bool = False,
    ) -> dict:
        """Gọi LLM và parse JSON từ response."""
        import json
        import re

        full_prompt = prompt + "\n\nRespond with valid JSON only. Do not include thinking tags."

        response = await self.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            use_grader=use_grader,
        )

        response = response.strip()

        # Loại bỏ thinking tags
        response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
        response = response.strip()

        # Xử lý markdown code blocks
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            response = json_match.group()

        return json.loads(response.strip())

    async def health_check(self) -> dict[str, bool]:
        """Kiểm tra kết nối tới vLLM server.

        vLLM expose:
          - GET /health → {"status": "healthy"}
          - GET /v1/models → danh sách models
        """
        results = {
            "vllm_server": False,
            "main_model": False,
            "grader_model": False,
        }

        # base_url dạng "http://host:8001/v1" → server_url = "http://host:8001"
        server_url = self.base_url.rstrip("/").removesuffix("/v1")

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Kiểm tra /health endpoint
                health_resp = await client.get(f"{server_url}/health")
                if health_resp.status_code == 200:
                    results["vllm_server"] = True

                # Lấy danh sách models đang serve
                models_resp = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {settings.vllm_api_key}"},
                )
                if models_resp.status_code == 200:
                    data = models_resp.json()
                    available = [m["id"] for m in data.get("data", [])]

                    # So sánh tên model (có thể là tên ngắn hoặc full path)
                    main_base = self.main_model.split("/")[-1].lower()
                    grader_base = self.grader_model.split("/")[-1].lower()

                    for model_id in available:
                        model_lower = model_id.lower()
                        if main_base in model_lower or model_lower in main_base:
                            results["main_model"] = True
                        if grader_base in model_lower or model_lower in grader_base:
                            results["grader_model"] = True

        except Exception as e:
            logger.error(f"vLLM health check failed: {e}")

        return results

    async def list_models(self) -> list[str]:
        """Liệt kê models đang available trên vLLM server."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {settings.vllm_api_key}"},
                )
                if response.status_code == 200:
                    data = response.json()
                    return [m["id"] for m in data.get("data", [])]
        except Exception as e:
            logger.error(f"Failed to list vLLM models: {e}")
        return []


# Global instance
_llm_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Lấy global LLM service instance."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMService()
    return _llm_instance
