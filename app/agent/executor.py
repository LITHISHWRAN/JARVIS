from collections.abc import Iterator
from typing import Any

from app.agent.tool_calls import (ToolCall, ToolCallAccumulator)
from app.config import CONFIG
from app.core.context import ContextManager
from app.core.state import ConversationState
from app.llm.llama_cpp import LocalLLM
from app.tools.registry import ToolRegistry
from app.security.policy import SecurityPolicy

class AgentExecutor:
    """
    Executes an LLM-driven tool loop.
    Supports both normal and streaming execution.
    """

    def __init__(
        self,
        llm: LocalLLM,
        tools: ToolRegistry,
        state: ConversationState,
        context: ContextManager,
        security: SecurityPolicy,
    ):
        self.llm = llm
        self.tools = tools
        self.state = state
        self.context = context
        self.security = security

        self.max_steps = (
            CONFIG.llm.max_agent_steps
        )

    def run(
        self,
        enable_thinking: bool | None = None,
    ) -> str:

        self.state.task_active = True
        self.state.agent_step = 0

        try:
            while (
                self.state.agent_step
                < self.max_steps
            ):
                self.state.agent_step += 1

                context = self.context.build(
                    self.state.messages
                )

                response = self.llm.generate(
                    messages=context,
                    tools=self.tools.schemas(),
                    enable_thinking=enable_thinking,
                )

                message = response.choices[0].message

                if not message.tool_calls:
                    content = (
                        message.content or ""
                    )

                    self.state.messages.append(
                        {
                            "role": "assistant",
                            "content": content,
                        }
                    )

                    return content

                self._store_tool_call_message(
                    message
                )

                for raw_tool_call in (
                    message.tool_calls
                ):
                    tool_call = ToolCall(
                        id=raw_tool_call.id,
                        name=raw_tool_call.function.name,
                        arguments=self._parse_arguments(
                            raw_tool_call.function.arguments
                        ),
                    )

                    result = self._execute_tool(
                        tool_call
                    )

                    self._store_tool_result(
                        tool_call,
                        result,
                    )

            return (
                "I reached the maximum number "
                "of actions allowed for this task."
            )

        finally:
            self.state.task_active = False

    def run_stream(
        self,
        enable_thinking: bool | None = None,
    ) -> Iterator[str]:
        """
        Run the complete agent loop while streaming
        normal assistant text.

        Tool-call chunks are accumulated internally
        and are never exposed as user-facing text.
        """

        self.state.task_active = True
        self.state.agent_step = 0

        try:
            while (
                self.state.agent_step
                < self.max_steps
            ):
                self.state.agent_step += 1

                context = self.context.build(
                    self.state.messages
                )

                stream = self.llm.generate_stream(
                    messages=context,
                    tools=self.tools.schemas(),
                    enable_thinking=enable_thinking,
                )

                accumulator = (
                    ToolCallAccumulator()
                )

                text_parts = []

                assistant_role = None

                for chunk in stream:
                    if not chunk.choices:
                        continue

                    delta = chunk.choices[0].delta

                    if delta.role:
                        assistant_role = (
                            delta.role
                        )

                    if delta.content:
                        text_parts.append(
                            delta.content
                        )

                        yield delta.content

                    if delta.tool_calls:
                        accumulator.add(
                            delta.tool_calls
                        )

                tool_calls = (
                    accumulator.build()
                    if not accumulator.is_empty()
                    else []
                )

                complete_text = "".join(
                    text_parts
                )

                if not tool_calls:
                    self.state.messages.append(
                        {
                            "role": "assistant",
                            "content": complete_text,
                        }
                    )

                    return

                self._store_streamed_tool_message(
                    content=complete_text,
                    tool_calls=tool_calls,
                    role=assistant_role,
                )

                for tool_call in tool_calls:
                    result = self._execute_tool(
                        tool_call
                    )

                    self._store_tool_result(
                        tool_call,
                        result,
                    )

            yield (
                "\nI reached the maximum number "
                "of actions allowed for this task."
            )

        finally:
            self.state.task_active = False
            
    def _execute_tool(
        self,
        tool_call: ToolCall,
    ) -> str:

        self.state.last_tool_name = (
            tool_call.name
        )

        decision = self.security.check(
            tool_call.name
        )

        if not decision.allowed:
            result = (
                f"Tool execution denied: "
                f"{decision.reason}"
            )

            self.state.last_tool_result = result

            return result

        try:
            result = self.tools.execute(
                tool_call.name,
                tool_call.arguments,
            )

            self.state.last_tool_result = result

            if isinstance(result, str):
                return result

            return str(result)

        except Exception as exc:
            error = (
                f"Tool '{tool_call.name}' failed: "
                f"{type(exc).__name__}: {exc}"
            )

            self.state.last_tool_result = error

            return error


    def _store_tool_call_message(
        self,
        message: Any,
    ) -> None:

        tool_calls = []

        for call in message.tool_calls:
            tool_calls.append(
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": (
                            call.function.name
                        ),
                        "arguments": (
                            call.function.arguments
                        ),
                    },
                }
            )

        self.state.messages.append(
            {
                "role": "assistant",
                "content": (
                    message.content or ""
                ),
                "tool_calls": tool_calls,
            }
        )

    def _store_streamed_tool_message(
        self,
        content: str,
        tool_calls: list[ToolCall],
        role: str | None,
    ) -> None:

        calls = []

        for call in tool_calls:
            calls.append(
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": self._dump_arguments(
                            call.arguments
                        ),
                    },
                }
            )

        self.state.messages.append(
            {
                "role": "assistant",
                "content": content,
                "tool_calls": calls,
            }
        )

    def _store_tool_result(
        self,
        tool_call: ToolCall,
        result: str,
    ) -> None:

        self.state.messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
        )

    @staticmethod
    def _parse_arguments(
        raw_arguments: str | None,
    ) -> dict[str, Any]:

        import json

        raw_arguments = (
            raw_arguments or "{}"
        )

        arguments = json.loads(
            raw_arguments
        )

        if not isinstance(arguments, dict):
            raise ValueError(
                "Tool arguments must be a JSON object."
            )

        return arguments

    @staticmethod
    def _dump_arguments(
        arguments: dict[str, Any],
    ) -> str:

        import json

        return json.dumps(
            arguments,
            separators=(",", ":"),
        )

