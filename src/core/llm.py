"""vLLM LLM service wrapper cho TSBot.

vLLM chạy trên máy A100, expose OpenAI-compatible API.
Dùng ChatOpenAI từ langchain-openai để giao tiếp.
"""

import logging
from typing import Any, AsyncGenerator, Optional

import httpx
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings

logger = logging.getLogger(__name__)


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

    def _make_llm(self, model: str, temperature: float, top_p: Optional[float] = None) -> ChatOpenAI:
        """Tạo ChatOpenAI instance trỏ vào vLLM server."""
        kwargs: dict[str, Any] = {
            "base_url": self.base_url,
            "api_key": settings.vllm_api_key,
            "model": model,
            "temperature": temperature,
        }
        if top_p is not None:
            kwargs["model_kwargs"] = {"top_p": top_p}
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

        llm = self.grader_llm if use_grader else self.main_llm

        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("human", prompt))

        response = await llm.ainvoke(messages, **kwargs)
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
        llm = self.grader_llm if use_grader else self.main_llm

        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("human", prompt))

        async for chunk in llm.astream(messages, **kwargs):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content

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
