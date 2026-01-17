"""LLM Provider abstractions for conversation generation."""

import os
from abc import ABC, abstractmethod
from typing import Any

import httpx

from src.utils.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """
        Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            **kwargs: Additional provider-specific parameters.

        Returns:
            Generated text response.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama provider for local Llama models."""

    def __init__(self, model: str = "llama3.2", base_url: str | None = None) -> None:
        """Initialize Ollama provider."""
        self.model = model
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    @property
    def name(self) -> str:
        """Provider name."""
        return f"ollama/{self.model}"

    async def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Generate response using Ollama API."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    **kwargs,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]


class OpenAIProvider(LLMProvider):
    """OpenAI provider for GPT models."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None) -> None:
        """Initialize OpenAI provider."""
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    @property
    def name(self) -> str:
        """Provider name."""
        return f"openai/{self.model}"

    async def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Generate response using OpenAI API."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    **kwargs,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing and MVP development."""

    @property
    def name(self) -> str:
        """Provider name."""
        return "mock"

    async def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Generate mock responses based on conversation state."""
        # Count user messages to determine conversation stage
        user_messages = [m for m in messages if m["role"] == "user"]
        stage = len(user_messages)

        # Get last user message
        last_message = ""
        if user_messages:
            last_message = user_messages[-1]["content"].lower()

        # Mock conversation flow
        if stage == 0:
            return "Hello! I'm here to help you set up your lead generation profile. Could you tell me the name of your company?"

        elif stage == 1:
            return "Great! What industry does your company operate in?"

        elif stage == 2:
            return "Excellent. Now, could you describe your ideal customer? What kind of companies or individuals are you looking to work with?"

        elif stage == 3:
            return "That's helpful! What services does your company offer?"

        elif stage == 4:
            return "Perfect! Is there anything else you'd like me to know about your business or ideal clients?"

        elif "no" in last_message or "that's all" in last_message or "nothing" in last_message:
            return "Thank you for sharing all this information! I now have a good understanding of your business. To save your profile and start finding leads, please create an account."

        else:
            return "Thank you for that additional information. Is there anything else you'd like to add?"
