"""
Domain repository interfaces for LLM / OpenHands access.

Concrete implementations live in the infra layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import IssueEntity


class LlmRepository(ABC):
    """
    Abstraction for interacting with OpenHands and MCP providers.

    The implementation will encapsulate all external calls; the domain layer
    only depends on this interface.
    """

    @abstractmethod
    def check_mcp_connection(self, provider: str) -> bool:
        """Return True if the given MCP provider is connected."""

    @abstractmethod
    def connect_mcp(self, provider: str) -> None:
        """Connect the given MCP provider. Implementation details are infra-specific."""

    @abstractmethod
    def assign_agent(self, issue: IssueEntity, prompt: str) -> None:
        """
        Assign or trigger an agent in OpenHands for the given issue.

        The exact behavior will be implemented later.
        """


