"""LLM Service with provider failover."""

import os
from typing import Any

from src.services.llm_provider import (
    LLMProvider,
    MockLLMProvider,
    OllamaProvider,
    OpenAIProvider,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AllProvidersFailedError(Exception):
    """Raised when all LLM providers fail."""

    pass


class LLMService:
    """
    LLM Service with automatic failover.

    Tries providers in order until one succeeds:
    1. Ollama (local, free)
    2. OpenAI (paid)
    3. Mock (fallback for development)
    """

    def __init__(self, use_mock: bool | None = None) -> None:
        """
        Initialize LLM service with provider chain.

        Args:
            use_mock: Force mock provider. Defaults to LLM_USE_MOCK env var.
        """
        self._use_mock = use_mock if use_mock is not None else os.getenv("LLM_USE_MOCK", "").lower() == "true"
        self._providers: list[LLMProvider] | None = None

    @property
    def providers(self) -> list[LLMProvider]:
        """Get provider chain, lazily initialized."""
        if self._providers is None:
            if self._use_mock:
                self._providers = [MockLLMProvider()]
            else:
                self._providers = [
                    OllamaProvider(),
                    OpenAIProvider(),
                    MockLLMProvider(),  # Final fallback
                ]
        return self._providers

    async def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """
        Generate a response using the provider chain.

        Tries each provider in order until one succeeds.

        Args:
            messages: Conversation messages.
            **kwargs: Additional parameters for providers.

        Returns:
            Generated response text.

        Raises:
            AllProvidersFailedError: If all providers fail.
        """
        errors: list[tuple[str, str]] = []

        for provider in self.providers:
            try:
                logger.info("llm_generate_attempt", provider=provider.name)
                response = await provider.generate(messages, **kwargs)
                logger.info(
                    "llm_generate_success",
                    provider=provider.name,
                    response_length=len(response),
                )
                return response

            except Exception as e:
                error_msg = str(e)
                errors.append((provider.name, error_msg))
                logger.warning(
                    "llm_generate_failed",
                    provider=provider.name,
                    error=error_msg,
                )
                continue

        # All providers failed
        logger.exception(
            "all_llm_providers_failed",
            errors=errors,
        )
        raise AllProvidersFailedError(f"All LLM providers failed: {errors}")
