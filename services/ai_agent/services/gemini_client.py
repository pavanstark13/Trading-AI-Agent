"""Google Gemini AI client — free tier, 1,500 requests/day."""

import json
from typing import Any

import google.generativeai as genai
import structlog
from google.generativeai.types import GenerateContentResponse

from services.ai_agent.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class GeminiClient:
    """
    Async-compatible Gemini client wrapping the google-generativeai SDK.

    Gemini free tier limits (gemini-1.5-flash):
      - 1,500 requests/day
      - 1M tokens/minute
      - 15 requests/minute
    """

    def __init__(self) -> None:
        genai.configure(api_key=settings.gemini_api_key)
        self._model_name = settings.gemini_model
        self._max_tokens = settings.max_tokens
        self._temperature = settings.temperature

    def _get_model(self, tools: list[dict] | None = None) -> genai.GenerativeModel:
        generation_config = genai.GenerationConfig(
            max_output_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        # Convert tool dicts to Gemini function declarations
        gemini_tools = None
        if tools:
            gemini_tools = self._convert_tools(tools)

        return genai.GenerativeModel(
            model_name=self._model_name,
            generation_config=generation_config,
            tools=gemini_tools,
        )

    def _convert_tools(self, tools: list[dict]) -> list:
        """Convert Anthropic-style tool dicts to Gemini function declarations."""
        from google.generativeai.types import FunctionDeclaration, Tool  # noqa: PLC0415

        declarations = []
        for tool in tools:
            params = tool.get("input_schema", {})
            declarations.append(
                FunctionDeclaration(
                    name=tool["name"],
                    description=tool.get("description", ""),
                    parameters=params,
                )
            )
        return [Tool(function_declarations=declarations)]

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> GenerateContentResponse:
        """Send a chat request to Gemini."""
        import asyncio  # noqa: PLC0415

        model = self._get_model(tools)

        # Build conversation history for Gemini
        history = []
        for msg in messages[:-1]:  # all but last message
            role = "user" if msg["role"] == "user" else "model"
            content = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
            history.append({"role": role, "parts": [content]})

        # Start chat with system prompt prepended to first message
        chat = model.start_chat(history=history)

        # Last user message
        last_msg = messages[-1] if messages else {"content": ""}
        user_content = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)

        # Prepend system prompt to first user turn if no history
        full_message = f"{system_prompt}\n\n---\n\n{user_content}" if not history else user_content

        logger.debug("Sending Gemini request", model=self._model_name)

        # Gemini SDK is synchronous — run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: chat.send_message(full_message),
        )

        logger.debug(
            "Gemini response received",
            finish_reason=str(response.candidates[0].finish_reason)
            if response.candidates
            else "unknown",
        )
        return response

    def extract_text(self, response: GenerateContentResponse) -> str:
        """Extract text from a Gemini response."""
        try:
            return response.text
        except Exception:
            if response.candidates:
                parts = response.candidates[0].content.parts
                return " ".join(p.text for p in parts if hasattr(p, "text"))
            return ""

    def extract_tool_calls(self, response: GenerateContentResponse) -> list[dict[str, Any]]:
        """Extract function call blocks from a Gemini response."""
        tool_calls = []
        if not response.candidates:
            return tool_calls
        for part in response.candidates[0].content.parts:
            if part.function_call:
                fc = part.function_call
                tool_calls.append(
                    {
                        "id": fc.name,
                        "name": fc.name,
                        "input": dict(fc.args),
                    }
                )
        return tool_calls

    async def chat_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]],
        tool_executor: Any,
        max_rounds: int = 5,
    ) -> tuple[str, list[dict]]:
        """
        Agentic loop: chat with tool use until model stops calling tools.
        Returns (final_text, tool_call_history).
        """
        import asyncio  # noqa: PLC0415

        model = self._get_model(tools)
        chat = model.start_chat(history=[])
        tool_history: list[dict] = []

        first_message = f"{system_prompt}\n\n---\n\n{user_message}"

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: chat.send_message(first_message))

        for _ in range(max_rounds):
            tool_calls = self.extract_tool_calls(response)

            if not tool_calls:
                return self.extract_text(response), tool_history

            # Execute each tool call
            tool_results = []
            for tc in tool_calls:
                logger.info("Executing tool", name=tc["name"])
                try:
                    result = await tool_executor(tc["name"], tc["input"])
                    result_str = (
                        json.dumps(result, default=str) if isinstance(result, dict) else str(result)
                    )
                    tool_results.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tc["name"],
                                response={"result": result_str},
                            )
                        )
                    )
                    tool_history.append(
                        {"tool": tc["name"], "input": tc["input"], "result": result}
                    )
                except Exception as e:
                    logger.error("Tool execution failed", tool=tc["name"], error=str(e))
                    tool_results.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tc["name"],
                                response={"error": str(e)},
                            )
                        )
                    )

            response = await loop.run_in_executor(None, lambda: chat.send_message(tool_results))

        return self.extract_text(response), tool_history


_gemini_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    global _gemini_client  # noqa: PLW0603
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
