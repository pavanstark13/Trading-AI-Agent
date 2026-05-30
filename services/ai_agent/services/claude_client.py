"""Anthropic Claude API client with prompt caching support."""

from typing import Any

import structlog
from anthropic import AsyncAnthropic
from anthropic.types import Message, TextBlock

from services.ai_agent.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class ClaudeClient:
    """
    Async Claude API client with prompt caching.

    Uses cache_control on system prompts to reduce latency and costs
    when the same system prompt is reused across requests.
    """

    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.claude_model
        self._max_tokens = settings.max_tokens

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        use_prompt_cache: bool = True,
    ) -> Message:
        """
        Send a chat request to Claude with optional prompt caching.

        When use_prompt_cache=True, the system prompt is cached using
        cache_control: {"type": "ephemeral"} which caches for 5 minutes.
        This is ideal for long system prompts reused across many requests.
        """
        # Build system with optional cache control
        if use_prompt_cache:
            system: list[dict] | str = [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        else:
            system = system_prompt

        request_params: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "system": system,
            "messages": messages,
        }

        if temperature is not None:
            request_params["temperature"] = temperature
        elif hasattr(settings, "temperature"):
            request_params["temperature"] = settings.temperature

        if tools:
            request_params["tools"] = tools

        logger.debug("Sending Claude request", model=self._model, use_cache=use_prompt_cache)

        response = await self._client.messages.create(**request_params)

        logger.debug(
            "Claude response received",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cache_read_tokens=getattr(response.usage, "cache_read_input_tokens", 0),
            cache_write_tokens=getattr(response.usage, "cache_creation_input_tokens", 0),
            stop_reason=response.stop_reason,
        )

        return response

    def extract_text(self, response: Message) -> str:
        """Extract text content from a Claude response."""
        for block in response.content:
            if isinstance(block, TextBlock):
                return block.text
        return ""

    def extract_tool_use(self, response: Message) -> list[dict[str, Any]]:
        """Extract tool use blocks from a Claude response."""
        tool_uses = []
        for block in response.content:
            if block.type == "tool_use":
                tool_uses.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        return tool_uses

    async def chat_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]],
        tool_executor: Any,
        max_rounds: int = 5,
    ) -> tuple[str, list[dict]]:
        """
        Agentic loop: chat with tool use until completion.

        Handles multi-turn tool calls automatically.
        Returns (final_text, tool_call_history).
        """
        messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
        tool_history: list[dict] = []

        for round_num in range(max_rounds):
            response = await self.chat(
                system_prompt=system_prompt,
                messages=messages,
                tools=tools,
                use_prompt_cache=True,
            )

            tool_uses = self.extract_tool_use(response)

            if not tool_uses or response.stop_reason == "end_turn":
                # Final response
                final_text = self.extract_text(response)
                return final_text, tool_history

            # Execute tools
            tool_results = []
            for tool_call in tool_uses:
                logger.info("Executing tool", name=tool_call["name"], round=round_num)
                try:
                    result = await tool_executor(tool_call["name"], tool_call["input"])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": str(result),
                    })
                    tool_history.append({
                        "tool": tool_call["name"],
                        "input": tool_call["input"],
                        "result": result,
                    })
                except Exception as e:
                    logger.error("Tool execution failed", tool=tool_call["name"], error=str(e))
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": f"Error: {e}",
                        "is_error": True,
                    })

            # Add assistant message and tool results to conversation
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        # Fallback: get final response
        response = await self.chat(system_prompt=system_prompt, messages=messages, use_prompt_cache=True)
        return self.extract_text(response), tool_history


_claude_client: ClaudeClient | None = None


def get_claude_client() -> ClaudeClient:
    global _claude_client  # noqa: PLW0603
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
