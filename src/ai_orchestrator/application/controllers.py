"""
HTTP controllers for the application layer.

These are thin wrappers that adapt FastAPI requests into domain calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, TypedDict

from ai_orchestrator.domain.models import IssueEventDTO, IssueEntity
from ai_orchestrator.domain.services import OrchestratorService, McpStartupService


class JiraIssuePriority(TypedDict, total=False):
    self: str
    iconUrl: str
    name: str
    id: str


class JiraIssueFields(TypedDict, total=False):
    summary: str
    created: str
    description: str
    labels: List[str]
    priority: JiraIssuePriority


class JiraIssue(TypedDict):
    id: str
    self: str
    key: str
    fields: JiraIssueFields


class JiraIssueWebhookPayload(TypedDict):
    issue: JiraIssue


@dataclass
class IssueController:
    """
    Controller responsible for handling Jira issue webhook events.
    """

    orchestrator_service: OrchestratorService
    mcp_startup_service: McpStartupService

    def handle_issue_created(self, payload: JiraIssueWebhookPayload) -> None:
        """
        Entry point for the 'issue-created' webhook.

        The actual mapping from payload to IssueEntity/IssueEventDTO will be
        implemented later.
        """
        # TODO: map payload to IssueEntity , then delegate to orchestrator_service
        return None

    def handle_issue_updated(self, payload: JiraIssueWebhookPayload) -> None:
        """
        Entry point for the 'issue-updated' webhook.
        """
        # TODO: map payload to IssueEntity , then delegate to orchestrator_service
        return None

    def init_mcps(self) -> None:
        """
        Explicit hook to initialize MCP connections.

        This mirrors the class diagram method `initMCPs`.
        """
        # TODO: delegate to mcp_startup_service.on_startup
        return None


