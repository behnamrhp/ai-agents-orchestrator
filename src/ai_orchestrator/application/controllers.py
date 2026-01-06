"""
HTTP controllers for the application layer.

These are thin wrappers that adapt FastAPI requests into domain calls.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, TypedDict

from ai_orchestrator.domain.models import IssueEventDTO, IssueEntity
from ai_orchestrator.domain.services import OrchestratorService, McpStartupService

logger = logging.getLogger(__name__)


class JiraIssuePriority(TypedDict, total=False):
    self: str
    iconUrl: str
    name: str
    id: str


class JiraIssueStatus(TypedDict, total=False):
    """Jira issue status object structure."""
    self: str
    description: str
    iconUrl: str
    name: str
    id: str


class JiraIssueFields(TypedDict, total=False):
    summary: str
    created: str
    description: str
    labels: List[str]
    priority: JiraIssuePriority
    status: JiraIssueStatus


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

    def _map_jira_payload_to_issue_entity(self, jira_issue: JiraIssue) -> IssueEntity:
        """
        Map Jira webhook payload to domain IssueEntity.

        Extracts issue data from the Jira webhook format and converts it
        to the domain model format.

        Args:
            jira_issue: The Jira issue from the webhook payload

        Returns:
            A domain IssueEntity instance
        """
        fields = jira_issue.get("fields", {})
        issue_key = jira_issue.get("key", "")

        # Extract project key from issue key (format: PROJECT-123)
        project_key = ""
        if issue_key and "-" in issue_key:
            project_key = issue_key.split("-")[0]

        # Extract status from fields
        # Jira webhooks include status as an object with a "name" field
        status = ""
        status_obj = fields.get("status")
        if status_obj and isinstance(status_obj, dict):
            status = status_obj.get("name", "")
        elif status_obj:
            status = str(status_obj)

        # Extract labels
        labels = fields.get("labels", [])
        if not isinstance(labels, list):
            labels = []

        # Extract description (can be None or empty)
        description = fields.get("description", "") or ""

        # Extract summary
        summary = fields.get("summary", "") or ""

        # Note: Additional URLs (project_repo_url, prd_url, etc.) are not in the
        # standard Jira webhook payload. These would need to be extracted from
        # custom fields or the description if they're embedded there.
        # For now, we leave them as None and they can be populated later if needed.

        return IssueEntity(
            id=jira_issue.get("id", ""),
            key=issue_key,
            project_key=project_key,
            status=status,
            labels=labels,
            summary=summary,
            description=description,
            project_repo_url=None,  # Not in standard webhook payload
            team_contribution_rules_url=None,  # Not in standard webhook payload
            team_architecture_rules_url=None,  # Not in standard webhook payload
            prd_url=None,  # Not in standard webhook payload
            ard_url=None,  # Not in standard webhook payload
        )

    def handle_issue_created(self, payload: JiraIssueWebhookPayload) -> None:
        """
        Entry point for the 'issue-created' webhook.

        Per the sequence diagram:
        1. Map payload to IssueEntity and IssueEventDTO
        2. Delegate to orchestrator_service.handle_issue_created(eventDto)

        Args:
            payload: The Jira webhook payload for issue created event
        """
        logger.info("Received issue-created webhook")

        try:
            # Map payload to domain models
            jira_issue = payload.get("issue", {})
            if not jira_issue:
                logger.error("Invalid webhook payload: missing 'issue' field")
                return

            issue_entity = self._map_jira_payload_to_issue_entity(jira_issue)
            logger.info("Mapped Jira payload to IssueEntity: %s", issue_entity.key)

            # Create event DTO
            event_dto = IssueEventDTO(issue=issue_entity, event_type="issue_created")

            # Delegate to orchestrator service
            self.orchestrator_service.handle_issue_created(event_dto)

            logger.info("Successfully processed issue-created webhook for %s", issue_entity.key)

        except Exception as e:
            logger.error(
                "Error processing issue-created webhook: %s",
                e,
                exc_info=True,
            )
            # Re-raise to allow FastAPI to return appropriate error response
            raise

    def handle_issue_updated(self, payload: JiraIssueWebhookPayload) -> None:
        """
        Entry point for the 'issue-updated' webhook.

        Per the sequence diagram:
        1. Map payload to IssueEntity and IssueEventDTO
        2. Delegate to orchestrator_service.handle_issue_updated(eventDto)

        Args:
            payload: The Jira webhook payload for issue updated event
        """
        logger.info("Received issue-updated webhook")

        try:
            # Map payload to domain models
            jira_issue = payload.get("issue", {})
            if not jira_issue:
                logger.error("Invalid webhook payload: missing 'issue' field")
                return

            issue_entity = self._map_jira_payload_to_issue_entity(jira_issue)
            logger.info("Mapped Jira payload to IssueEntity: %s", issue_entity.key)

            # Create event DTO
            event_dto = IssueEventDTO(issue=issue_entity, event_type="issue_updated")

            # Delegate to orchestrator service
            self.orchestrator_service.handle_issue_updated(event_dto)

            logger.info("Successfully processed issue-updated webhook for %s", issue_entity.key)

        except Exception as e:
            logger.error(
                "Error processing issue-updated webhook: %s",
                e,
                exc_info=True,
            )
            # Re-raise to allow FastAPI to return appropriate error response
            raise

    def init_mcps(self) -> None:
        """
        Explicit hook to initialize MCP connections.

        Per the sequence diagram, this is called during startup to ensure
        MCP providers (e.g., Atlassian) are connected before serving requests.

        This mirrors the class diagram method `initMCPs`.
        """
        logger.info("Initializing MCP connections via McpStartupService")
        self.mcp_startup_service.on_startup()
        logger.info("MCP initialization completed")


