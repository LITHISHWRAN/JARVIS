from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """
    Base interface for every JARVIS tool.

    A tool has three responsibilities:

        1. Describe itself to the LLM.
        2. Validate/receive arguments.
        3. Execute an action and return a result.

    The tool itself does not decide when it should be called.
    That decision belongs to the agent/LLM.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique tool name exposed to the LLM.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human/LLM-readable description of what the tool does.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """
        JSON Schema describing the tool arguments.
        """
        raise NotImplementedError

    def schema(self) -> dict[str, Any]:
        """
        Return the OpenAI-compatible function tool schema.
        """

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    @abstractmethod
    def execute(
        self,
        arguments: dict[str, Any],
    ) -> Any:
        """
        Execute the tool.

        The registry is responsible for finding the tool.
        The tool is responsible for performing its own action.
        """
        raise NotImplementedError
