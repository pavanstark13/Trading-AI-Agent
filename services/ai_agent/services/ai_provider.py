"""
AI provider factory.

Switch providers by setting AI_PROVIDER in .env:
  AI_PROVIDER=gemini   → Google Gemini (free tier, default)
  AI_PROVIDER=claude   → Anthropic Claude (paid, production)
"""

from typing import Any, Protocol, runtime_checkable

from services.ai_agent.config import get_settings

settings = get_settings()


@runtime_checkable
class AIProvider(Protocol):
    """Common interface all AI providers must satisfy."""

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any: ...

    def extract_text(self, response: Any) -> str: ...

    def extract_tool_calls(self, response: Any) -> list[dict[str, Any]]: ...

    async def chat_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]],
        tool_executor: Any,
        max_rounds: int = 5,
    ) -> tuple[str, list[dict]]: ...


def get_ai_provider() -> AIProvider:
    """Return the configured AI provider instance."""
    provider = settings.ai_provider.lower()

    if provider == "gemini":
        from services.ai_agent.services.gemini_client import get_gemini_client  # noqa: PLC0415

        return get_gemini_client()  # type: ignore[return-value]

    elif provider == "claude":
        from services.ai_agent.services.claude_client import get_claude_client  # noqa: PLC0415

        return get_claude_client()  # type: ignore[return-value]

    else:
        raise ValueError(f"Unknown AI_PROVIDER='{provider}'. Valid options: 'gemini', 'claude'")
