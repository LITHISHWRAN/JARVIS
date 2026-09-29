from typing import Any

from app.config import CONFIG


class ContextManager:
    """
    Controls the messages sent to the LLM.

    Responsibilities:
        - Keep the system prompt
        - Keep recent conversation history
        - Respect the configured history limits
        - Reserve context for the model response
        - Prepare context for future tool schemas and agent state

    This class does not call the LLM.
    """

    def __init__(self):
        self.max_history_turns = (
            CONFIG.llm.max_history_turns
        )

        self.history_token_budget = (
            CONFIG.llm.history_token_budget
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Build the final message list that will be sent to the LLM.
        """

        if not messages:
            return []

        system_message = self._get_system_message(
            messages
        )

        conversation = self._get_conversation_messages(
            messages
        )

        conversation = self._limit_turns(
            conversation
        )

        conversation = self._fit_token_budget(
            conversation
        )

        result = []

        if system_message:
            result.append(system_message)

        result.extend(conversation)

        return result

    # ------------------------------------------------------------------
    # System prompt
    # ------------------------------------------------------------------

    @staticmethod
    def _get_system_message(
        messages: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """
        Return the first system message.

        Only one system message is currently expected.
        """

        for message in messages:

            if message.get("role") == "system":
                return message

        return None

    # ------------------------------------------------------------------
    # Conversation
    # ------------------------------------------------------------------

    @staticmethod
    def _get_conversation_messages(
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Return all non-system messages.
        """

        return [
            message
            for message in messages
            if message.get("role") != "system"
        ]

    # ------------------------------------------------------------------
    # Turn limiting
    # ------------------------------------------------------------------

    def _limit_turns(
        self,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Keep only the most recent conversational turns.

        A turn consists of:

            user
            assistant

        Tool messages will be handled more carefully once the
        tool execution system is implemented.
        """

        if not messages:
            return []

        max_messages = self.max_history_turns * 2

        if len(messages) <= max_messages:
            return messages

        return messages[-max_messages:]

    # ------------------------------------------------------------------
    # Token budget
    # ------------------------------------------------------------------

    def _fit_token_budget(
        self,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Keep recent messages until the approximate history
        token budget is exhausted.

        This is intentionally an approximation for now.

        A real tokenizer-based implementation will replace this
        once we integrate the exact Qwen3 tokenizer.
        """

        if not messages:
            return []

        selected = []

        estimated_tokens = 0

        for message in reversed(messages):

            message_tokens = self._estimate_tokens(
                message
            )

            if (
                selected
                and estimated_tokens + message_tokens
                > self.history_token_budget
            ):
                break

            selected.append(message)

            estimated_tokens += message_tokens

        selected.reverse()

        return selected

    # ------------------------------------------------------------------
    # Token estimation
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_tokens(
        message: dict[str, Any],
    ) -> int:
        """
        Rough token estimate.

        A common approximation for English text is
        approximately 4 characters per token.

        This is NOT the final tokenizer implementation.
        """

        content = message.get(
            "content",
            "",
        )

        if not isinstance(content, str):
            content = str(content)

        return max(
            1,
            len(content) // 4,
        )