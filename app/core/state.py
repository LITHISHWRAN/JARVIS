from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationState:
    """
    Runtime state for one JARVIS conversation.

    This object contains conversation data and task execution state.
    It does not contain model-specific logic.
    """

    # -----------------------------------------------------------------------
    # Conversation
    # -----------------------------------------------------------------------

    messages: list[dict[str, Any]] = field(
        default_factory=list
    )

    # -----------------------------------------------------------------------
    # Current task
    # -----------------------------------------------------------------------

    current_task: str | None = None

    agent_step: int = 0

    # -----------------------------------------------------------------------
    # Tool execution
    # -----------------------------------------------------------------------

    last_tool_name: str | None = None

    last_tool_result: Any = None

    # -----------------------------------------------------------------------
    # Execution state
    # -----------------------------------------------------------------------

    task_active: bool = False

    waiting_for_confirmation: bool = False

    confirmation_data: dict[str, Any] | None = None

    # -----------------------------------------------------------------------
    # Runtime metadata
    # -----------------------------------------------------------------------

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def reset_task(self) -> None:
        """
        Reset only the current task execution state.

        Conversation history remains intact.
        """

        self.current_task = None
        self.agent_step = 0

        self.last_tool_name = None
        self.last_tool_result = None

        self.task_active = False

        self.waiting_for_confirmation = False
        self.confirmation_data = None
