"""Unit tests for Market Analyst Agent."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.ai_agent.agents.market_analyst import MarketAnalystAgent


class TestMarketAnalystAgent:
    """Tests for MarketAnalystAgent."""

    def setup_method(self):
        self.agent = MarketAnalystAgent()

    def test_init(self):
        """Agent should initialize with correct attributes."""
        assert self.agent.name == "MarketAnalyst"
        assert self.agent.agent_type == "market_analyst"

    def test_system_prompt_not_empty(self):
        """System prompt should be a non-empty string."""
        prompt = self.agent.system_prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_system_prompt_contains_key_concepts(self):
        """System prompt should mention key trading concepts."""
        prompt = self.agent.system_prompt
        assert "market" in prompt.lower()
        assert "risk" in prompt.lower()

    def test_tools_are_list(self):
        """Tools should be a list of tool definitions."""
        tools = self.agent.tools
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_tools_have_required_fields(self):
        """Each tool should have name, description, and input_schema."""
        for tool in self.agent.tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert isinstance(tool["name"], str)
            assert len(tool["name"]) > 0

    @pytest.mark.asyncio
    async def test_run_returns_dict(self):
        """run() should return a dict even if Claude API fails."""
        # Mock the Claude client to avoid API calls
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = []
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)
        mock_response.stop_reason = "end_turn"
        mock_client.chat = AsyncMock(return_value=mock_response)
        mock_client.extract_text = MagicMock(return_value="Mock market analysis complete.")
        mock_client.extract_tool_use = MagicMock(return_value=[])
        mock_client.chat_with_tools = AsyncMock(return_value=("Mock analysis", []))

        self.agent._client = mock_client

        context = {"tickers": ["AAPL"], "account_equity": 100000.0}
        result = await self.agent.run(context)

        assert isinstance(result, dict)
        assert "agent" in result
        assert result["agent"] == "MarketAnalyst"

    @pytest.mark.asyncio
    async def test_run_handles_error_gracefully(self):
        """run() should handle errors gracefully without raising."""
        mock_client = AsyncMock()
        mock_client.chat_with_tools = AsyncMock(side_effect=Exception("API Error"))
        self.agent._client = mock_client

        context = {"tickers": ["AAPL"]}
        result = await self.agent.run(context)

        assert isinstance(result, dict)
        assert "error" in result or "analysis" in result

    def test_format_context_as_message(self):
        """_format_context_as_message should return non-empty string."""
        context = {"market": {"price": 100}, "tickers": ["AAPL"]}
        message = self.agent._format_context_as_message(context)
        assert isinstance(message, str)
        assert len(message) > 0
        assert "AAPL" in message
