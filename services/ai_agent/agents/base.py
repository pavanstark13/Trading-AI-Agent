"""Base agent class using Claude API."""

from abc import ABC, abstractmethod
from typing import Any

import structlog

from services.ai_agent.services.claude_client import ClaudeClient, get_claude_client

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base agent powered by Claude.

    Each agent has:
    - A specialized system prompt (cached for efficiency)
    - Tool definitions for interacting with the platform
    - A decision-making method that calls Claude
    """

    def __init__(self, name: str, agent_type: str) -> None:
        self.name = name
        self.agent_type = agent_type
        self._client: ClaudeClient = get_claude_client()

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt for this agent (will be cached)."""
        ...

    @property
    def tools(self) -> list[dict[str, Any]]:
        """Tool definitions available to this agent."""
        return []

    @abstractmethod
    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute agent logic given context.

        Args:
            context: Dict with market data, portfolio state, etc.

        Returns:
            Dict with agent decision and reasoning.
        """
        ...

    async def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        """Execute a named tool. Override to implement custom tool handlers."""
        logger.warning("Tool execution not implemented", agent=self.name, tool=tool_name)
        return {"error": f"Tool {tool_name} not implemented"}

    def _format_context_as_message(self, context: dict[str, Any]) -> str:
        """Format context dict as a user message for the agent."""
        import json  # noqa: PLC0415
        return f"Current context:\n{json.dumps(context, indent=2, default=str)}"

    async def _decide(
        self,
        user_message: str,
        additional_context: dict[str, Any] | None = None,
    ) -> tuple[str, list[dict]]:
        """Make a decision using Claude with tool use."""
        if self.tools:
            text, tool_history = await self._client.chat_with_tools(
                system_prompt=self.system_prompt,
                user_message=user_message,
                tools=self.tools,
                tool_executor=self.execute_tool,
            )
            return text, tool_history
        else:
            from anthropic.types import Message  # noqa: PLC0415
            response: Message = await self._client.chat(
                system_prompt=self.system_prompt,
                messages=[{"role": "user", "content": user_message}],
                use_prompt_cache=True,
            )
            return self._client.extract_text(response), []
