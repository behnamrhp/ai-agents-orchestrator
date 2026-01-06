"""
Concrete implementation of the LlmRepository interface for OpenHands.

All real communication with OpenHands and Atlassian MCP will be added later.
"""

from __future__ import annotations

from typing import Any

from ai_orchestrator.domain.models import IssueEntity
from ai_orchestrator.domain.repositories import LlmRepository


class OpenHandsLlmRepository(LlmRepository):
    """
    OpenHands-backed implementation of the LlmRepository interface.
    """

    def __init__(self, client: Any | None = None) -> None:
        """
        Optionally accept a low-level OpenHands client.

        The exact type and configuration will be defined later.
        """
        self._client = client

    def check_mcp_connection(self, provider: str) -> bool:
        """
        Check if the specified MCP provider is connected in OpenHands.
        """
        # TODO: implement connection check via OpenHands SDK
        return False

    def connect_mcp(self, provider: str) -> None:
        """
        Establish a connection for the specified MCP provider.
        """
        # TODO: implement MCP connection via OpenHands SDK
        return None

    def assign_agent(self, issue: IssueEntity, prompt: str) -> None:
        """
        Assign an agent in OpenHands for the given issue.
        """
        # TODO: implement agent assignment via OpenHands SDK
        return None


