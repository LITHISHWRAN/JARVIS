from dataclasses import dataclass

@dataclass(frozen=True)
class SecurityDecision:
    allowed: bool
    reason: str

class SecurityPolicy:
    """
    Initial JARVIS security policy.
    This is intentionally simple for M3.
    The policy decides whether a tool is allowed to execute.
    Confirmation workflows will be added later if required.
    """

    def __init__(self):
        self.blocked_tools: set[str] = set()

    def check(
        self,
        tool_name: str,
    ) -> SecurityDecision:
        """
        Check whether a tool is allowed to execute.
        """

        if tool_name in self.blocked_tools:
            return SecurityDecision(
                allowed=False,
                reason=(
                    f"Tool '{tool_name}' is blocked "
                    "by the security policy."
                ),
            )

        return SecurityDecision(
            allowed=True,
            reason="Tool is allowed.",
        )

    def block(
        self,
        tool_name: str,
    ) -> None:
        self.blocked_tools.add(tool_name)

    def unblock(
        self,
        tool_name: str,
    ) -> None:
        self.blocked_tools.discard(tool_name)
