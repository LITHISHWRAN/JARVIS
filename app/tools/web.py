import os
from typing import Any

from tavily import TavilyClient

from app.tools.base import Tool


class WebSearchManager:
    """
    Tavily-powered web search manager.

    The API key is loaded from the environment.
    """

    def __init__(self):
        self.api_key = os.environ.get(
            "TAVILY_API_KEY",
            "",
        ).strip()

        if not self.api_key:
            raise RuntimeError(
                "TAVILY_API_KEY is not configured."
            )

        self.client = TavilyClient(
            api_key=self.api_key
        )

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValueError(
                "Search query cannot be empty."
            )

        response = self.client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
        )

        return response.get(
            "results",
            [],
        )


class WebSearchTool(Tool):

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the live web for current or external "
            "information. Use this when the user asks for "
            "recent information, current events, websites, "
            "online information, or information that may not "
            "be available in the model's knowledge."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The exact web search query to perform."
                    ),
                },
                "max_results": {
                    "type": "integer",
                    "description": (
                        "Maximum number of search results "
                        "to return. Use between 1 and 10."
                    ),
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                },
            },
            "required": [
                "query",
            ],
        }

    def __init__(
        self,
        manager: WebSearchManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:
        query = arguments.get("query")

        if not query:
            raise ValueError(
                "The 'query' argument is required."
            )

        max_results = arguments.get(
            "max_results",
            5,
        )

        results = self.manager.search(
            query=query,
            max_results=max_results,
        )

        if not results:
            return (
                "No web search results were found."
            )

        formatted_results = []

        for index, result in enumerate(
            results,
            start=1,
        ):
            title = result.get(
                "title",
                "Untitled",
            )

            url = result.get(
                "url",
                "",
            )

            content = result.get(
                "content",
                "",
            )

            formatted_results.append(
                (
                    f"Result {index}\n"
                    f"Title: {title}\n"
                    f"URL: {url}\n"
                    f"Content: {content}"
                )
            )

        return "\n\n".join(
            formatted_results
        )
