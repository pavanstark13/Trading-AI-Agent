"""Unit tests for Market Analyst Agent."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.ai_agent.agents.market_analyst import MarketAnalystAgent


class TestMarketAnalystAgent:
    """Tests for MarketAnalystAgent."""

    def setup_method(self):
        # Patch the AI provider so no real API calls are made
        with patch("services.ai_agent.agents.base.get_ai_provider") as mock_provider_factory:
            self._mock_provider = AsyncMock()
            self._mock_provider.extract_text = MagicMock(return_value="Mock market analysis.")
            self._mock_provider.extract_tool_calls = MagicMock(return_value=[])
            self._mock_provider.chat_with_tools = AsyncMock(return_value=("Mock analysis", []))
            self._mock_provider.chat = AsyncMock(return_value=MagicMock())
            mock_provider_factory.return_value = self._mock_provider
            self.agent = MarketAnalystAgent()

    def test_init(self):
        assert self.agent.name == "MarketAnalyst"
        assert self.agent.agent_type == "market_analyst"

    def test_system_prompt_not_empty(self):
        prompt = self.agent.system_prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_system_prompt_contains_key_concepts(self):
        prompt = self.agent.system_prompt
        assert "market" in prompt.lower()
        assert "risk" in prompt.lower()

    def test_tools_are_list(self):
        tools = self.agent.tools
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_tools_have_required_fields(self):
        for tool in self.agent.tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert isinstance(tool["name"], str)
            assert len(tool["name"]) > 0

    @pytest.mark.asyncio
    async def test_run_returns_dict(self):
        """run() should return a dict with agent output."""
        self.agent._provider.chat_with_tools = AsyncMock(
            return_value=("Mock analysis complete.", [])
        )

        context = {"tickers": ["AAPL"], "account_equity": 100000.0}
        result = await self.agent.run(context)

        assert isinstance(result, dict)
        assert "agent" in result
        assert result["agent"] == "MarketAnalyst"

    @pytest.mark.asyncio
    async def test_run_handles_error_gracefully(self):
        """run() should catch errors and return error dict."""
        self.agent._provider.chat_with_tools = AsyncMock(side_effect=Exception("API Error"))

        context = {"tickers": ["AAPL"]}
        result = await self.agent.run(context)

        assert isinstance(result, dict)
        assert "error" in result or "analysis" in result

    def test_format_context(self):
        context = {"market": {"price": 100}, "tickers": ["AAPL"]}
        message = self.agent._format_context(context)
        assert isinstance(message, str)
        assert "AAPL" in message
