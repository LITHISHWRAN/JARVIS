from collections.abc import Iterator
from typing import Any

from openai import OpenAI

from app.config import CONFIG
from app.llm.base import LLM


class LocalLLM(LLM):
    """
    LLM client for the local llama.cpp server.

    llama.cpp exposes an OpenAI-compatible API, so the OpenAI
    Python client is used only as the HTTP client.

    The actual model remains completely local.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        enable_thinking: bool | None = None,
    ):
        self.client = OpenAI(
            base_url=base_url,
            api_key="local",
            timeout=CONFIG.llm.request_timeout,
            max_retries=1,
        )

        self.model = model

        self.enable_thinking = (
            CONFIG.llm.enable_thinking
            if enable_thinking is None
            else enable_thinking
        )

    # ------------------------------------------------------------------
    # Normal generation
    # ------------------------------------------------------------------

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        enable_thinking: bool | None = None,
    ):
        """
        Generate a complete response.

        Use this when the caller needs the complete response
        object, including tool-call information.
        """

        thinking = (
            self.enable_thinking
            if enable_thinking is None
            else enable_thinking
        )

        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools or None,
            extra_body={
                "chat_template_kwargs": {
                    "enable_thinking": thinking,
                },
            },
        )

    # ------------------------------------------------------------------
    # Streaming generation
    # ------------------------------------------------------------------
    def generate_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        enable_thinking: bool | None = None,
    ) -> Iterator[Any]:


        thinking = (
            self.enable_thinking
            if enable_thinking is None
            else enable_thinking
        )

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools or None,
            stream=True,
            extra_body={
                "chat_template_kwargs": {
                    "enable_thinking": thinking,
                },
            },
        )

        for chunk in stream:
            yield chunk
