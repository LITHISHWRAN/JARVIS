from typing import Any

from app.tools.base import Tool


class ToolRegistry:
    """
    Central registry for JARVIS tools.

    Responsibilities:

        - Register tools
        - Find tools by name
        - Generate LLM tool schemas
        - Execute a selected tool

    The registry does not contain the implementation of individual tools.
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, tool: Tool) -> None:
        """
        Register a tool.
        Tool names must be unique.
        """

        if tool.name in self._tools:
            raise ValueError(
                f"Tool already registered: {tool.name}"
            )

        self._tools[tool.name] = tool

    def register_many(
        self,
        tools: list[Tool],
    ) -> None:
        """
        Register multiple tools.
        """

        for tool in tools:
            self.register(tool)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(
        self,
        name: str,
    ) -> Tool:
        """
        Return a registered tool.

        Raises KeyError if the tool does not exist.
        """

        try:
            return self._tools[name]

        except KeyError:
            raise KeyError(
                f"Unknown JARVIS tool: {name}"
            )

    def has(
        self,
        name: str,
    ) -> bool:
        """
        Check whether a tool exists.
        """

        return name in self._tools

    def names(self) -> list[str]:
        """
        Return registered tool names.
        """

        return list(self._tools.keys())

    # ------------------------------------------------------------------
    # LLM schema
    # ------------------------------------------------------------------

    def schemas(self) -> list[dict[str, Any]]:
        """
        Return all registered tools in OpenAI-compatible format.
        """

        return [
            tool.schema()
            for tool in self._tools.values()
        ]

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """
        Find and execute a tool.
        """

        tool = self.get(name)

        return tool.execute(arguments)
