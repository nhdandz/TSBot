"""Ollama LLM wrapper for TSBot."""

import logging
from typing import Any, AsyncGenerator, Optional

import httpx
from langchain_ollama import ChatOllama
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Ollama LLM service wrapper with support for multiple models."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        main_model: Optional[str] = None,
        grader_model: Optional[str] = None,
    ):
        """Initialize LLM service.

        Args:
            base_url: Ollama server URL.
            main_model: Main generation model.
            grader_model: Grader/evaluation model.
        """
        self.base_url = base_url or settings.ollama_base_url
        self.main_model = main_model or settings.ollama_main_model
        self.grader_model = grader_model or settings.ollama_grader_model

        self._main_llm: Optional[ChatOllama] = None
        self._grader_llm: Optional[ChatOllama] = None

    @property
    def main_llm(self) -> ChatOllama:
        """Get main LLM for generation tasks."""
        if self._main_llm is None:
            self._main_llm = ChatOllama(
                base_url=self.base_url,
                model=self.main_model,
                temperature=settings.ollama_main_temperature,
                top_p=settings.ollama_main_top_p,
            )
        return self._main_llm

    @property
    def grader_llm(self) -> ChatOllama:
        """Get grader LLM for evaluation tasks (smaller, faster)."""
        if self._grader_llm is None:
            self._grader_llm = ChatOllama(
                base_url=self.base_url,
                model=self.grader_model,
                temperature=settings.ollama_grader_temperature,
            )
        return self._grader_llm

    def get_llm(
        self,
        model: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> ChatOllama:
        """Get a custom configured LLM instance.

        Args:
            model: Model name (defaults to main model).
            temperature: Generation temperature.
            **kwargs: Additional LLM parameters.

        Returns:
            Configured ChatOllama instance.
        """
        return ChatOllama(
            base_url=self.base_url,
            model=model or self.main_model,
            temperature=temperature,
            **kwargs,
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
        """Generate a response from the LLM.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.
            use_grader: Use grader model instead of main.
            **kwargs: Additional generation parameters.

        Returns:
            Generated text response.
        """
        llm = self.grader_llm if use_grader else self.main_llm

        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("human", prompt))

        response = await llm.ainvoke(messages, **kwargs)
        return response.content

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_grader: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream generate responses from the LLM.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.
            use_grader: Use grader model.
            **kwargs: Additional parameters.

        Yields:
            Text chunks as they're generated.
        """
        llm = self.grader_llm if use_grader else self.main_llm

        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("human", prompt))

        async for chunk in llm.astream(messages, **kwargs):
            if hasattr(chunk, "content"):
                yield chunk.content

    async def generate_with_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_grader: bool = False,
    ) -> dict:
        """Generate JSON response from LLM.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.
            use_grader: Use grader model.

        Returns:
            Parsed JSON response.
        """
        import json

        full_prompt = prompt + "\n\nRespond with valid JSON only."

        response = await self.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            use_grader=use_grader,
        )

        # Try to extract JSON from response
        response = response.strip()

        # Handle markdown code blocks
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        return json.loads(response.strip())

    async def health_check(self) -> dict[str, bool]:
        """Check if Ollama is running and models are available.

        Returns:
            Dict with model availability status.
        """
        results = {
            "ollama_server": False,
            "main_model": False,
            "grader_model": False,
        }

        try:
            async with httpx.AsyncClient() as client:
                # Check server
                response = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    results["ollama_server"] = True

                    # Check models
                    data = response.json()
                    available_models = [m["name"] for m in data.get("models", [])]

                    # Check main model (handle version suffixes)
                    main_base = self.main_model.split(":")[0]
                    for model in available_models:
                        if model.startswith(main_base):
                            results["main_model"] = True
                            break

                    # Check grader model
                    grader_base = self.grader_model.split(":")[0]
                    for model in available_models:
                        if model.startswith(grader_base):
                            results["grader_model"] = True
                            break

        except Exception as e:
            logger.error(f"LLM health check failed: {e}")

        return results

    async def list_models(self) -> list[str]:
        """List available models in Ollama.

        Returns:
            List of model names.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
        return []


# Global instance
_llm_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get global LLM service instance.

    Returns:
        LLMService instance.
    """
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMService()
    return _llm_instance
