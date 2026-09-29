import json
from dataclasses import dataclass
from typing import Any

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]

class ToolCallAccumulator:
    """
    Reconstructs tool calls received from a streaming LLM response.

    ```
    A single tool call may arrive across multiple chunks.
    """

    def __init__(self):
        self._calls: dict[int, dict[str, Any]] = {}

    def add(self, delta_tool_calls: list[Any]) -> None:
        for delta in delta_tool_calls:
            index = delta.index

            if index not in self._calls:
                self._calls[index] = {
                    "id": "",
                    "name": "",
                    "arguments": "",
                }

            call = self._calls[index]

            if delta.id:
                call["id"] = delta.id

            if delta.function:
                if delta.function.name:
                    call["name"] += delta.function.name

                if delta.function.arguments:
                    call["arguments"] += (
                        delta.function.arguments
                    )

    def is_empty(self) -> bool:
        return not self._calls

    def build(self) -> list[ToolCall]:
        result = []

        for index in sorted(self._calls):
            raw = self._calls[index]

            raw_arguments = (
                raw["arguments"] or "{}"
            )

            try:
                arguments = json.loads(
                    raw_arguments
                )
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON arguments for tool "
                    f"'{raw['name']}': "
                    f"{raw_arguments}"
                ) from exc

            if not isinstance(arguments, dict):
                raise ValueError(
                    f"Arguments for tool "
                    f"'{raw['name']}' must be an object."
                )

            result.append(
                ToolCall(
                    id=raw["id"],
                    name=raw["name"],
                    arguments=arguments,
                )
            )

        return result

    def parse_tool_call(
        tool_call: Any,
    ) -> ToolCall:

        call_id = tool_call.id

        function = tool_call.function

        name = function.name

        raw_arguments = (
            function.arguments or "{}"
        )

        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(
                    raw_arguments
                )
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON arguments for tool "
                    f"'{name}': {raw_arguments}"
                ) from exc
        else:
            arguments = raw_arguments

        if not isinstance(arguments, dict):
            raise ValueError(
                f"Arguments for tool "
                f"'{name}' must be a JSON object."
            )

        return ToolCall(
            id=call_id,
            name=name,
            arguments=arguments,
        )
