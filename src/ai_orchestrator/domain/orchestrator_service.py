"""
OrchestratorService definition in its own module.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import IssueEventDTO, IssueEntity
from .repositories import LlmRepository


@dataclass
class OrchestratorService:
    """
    Coordinates domain rules and interactions with the LLM repository.

    Core business logic will be implemented later.
    """

    llm_repository: LlmRepository

    def assign_agent(self, issue: IssueEntity, prompt: str) -> None:
        """
        Assign an agent for the given issue using the provided prompt.

        Implementation will later call into `self.llm_repository.assign_agent`.
        """
        # TODO: implement orchestration logic
        return None

    def handle_issue_created(self, event: IssueEventDTO) -> None:
        """
        Handle a newly created issue event.

        Will map the DTO to a domain IssueEntity and delegate to the LLM repository.
        """
        # TODO: implement issue-created business rules
        return None

    def handle_issue_updated(self, event: IssueEventDTO) -> None:
        """
        Handle an updated issue event.

        Will apply domain rules before delegating to the LLM repository.
        """
        # TODO: implement issue-updated business rules
        return None


