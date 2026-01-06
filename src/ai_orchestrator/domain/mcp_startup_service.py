"""
McpStartupService definition in its own module.
"""

from __future__ import annotations

from dataclasses import dataclass

from .repositories import LlmRepository


@dataclass
class McpStartupService:
    """
    Ensures required MCP providers (e.g., Atlassian) are connected during startup.
    """

    llm_repository: LlmRepository
    provider_name: str = "atlassian"

    def on_startup(self) -> None:
        """
        Startup hook that checks and establishes MCP connections as needed.
        """
        # TODO: implement startup MCP connection logic
        return None


