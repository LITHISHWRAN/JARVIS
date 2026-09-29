from datetime import datetime
from typing import Any

from app.tools.base import Tool


class GetTimeTool(Tool):
    """
    Return the current local system time.
    """

    @property
    def name(self) -> str:
        return "get_current_time"

    @property
    def description(self) -> str:
        return (
            "Get the current local date and time of the computer."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:

        now = datetime.now()

        return now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

