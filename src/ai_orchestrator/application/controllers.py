"""
HTTP controllers for the application layer.

These are thin wrappers that adapt FastAPI requests into domain calls.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict

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

    @staticmethod
    def _extract_project_identifier(summary: str, labels: List[str]) -> tuple[Optional[str], Optional[str]]:
        """
        Extract project identifier from issue summary or labels.

        Looks for patterns like `[backend]` or `[web-front]` in the issue summary.
        Falls back to checking labels if no bracket pattern is found.

        Args:
            summary: The issue summary/title
            labels: List of issue labels

        Returns:
            Tuple of (normalized_identifier, raw_identifier):
            - normalized_identifier: Uppercase with underscores (e.g., "BACKEND") for env var lookup
            - raw_identifier: Original identifier (e.g., "backend") for display/team_name
        """
        if not summary:
            summary = ""

        # Pattern: [identifier] at the start of summary
        # Example: "[backend] Add authentication" -> "backend"
        bracket_pattern = r"^\[([^\]]+)\]\s*"
        match = re.match(bracket_pattern, summary.strip())
        if match:
            raw_identifier = match.group(1).strip()
            normalized = IssueController._normalize_identifier(raw_identifier)
            logger.debug("Extracted project identifier '%s' (normalized: '%s') from summary pattern", raw_identifier, normalized)
            return normalized, raw_identifier

        # Fallback: check labels for common project identifiers
        # Look for labels that might indicate project (e.g., "backend", "frontend", "api")
        for label in labels:
            if label and isinstance(label, str):
                normalized = IssueController._normalize_identifier(label)
                # Check if there's an env var for this identifier
                env_var = f"PROJECT_REPO_{normalized}"
                if os.getenv(env_var):
                    logger.debug("Found project identifier '%s' (normalized: '%s') from label '%s'", label, normalized, label)
                    return normalized, label

        logger.debug("No project identifier found in summary or labels")
        return None, None

    @staticmethod
    def _normalize_identifier(identifier: str) -> str:
        """
        Normalize project identifier for environment variable lookup.

        Converts to uppercase and replaces hyphens with underscores.
        Example: "web-front" -> "WEB_FRONT"

        Args:
            identifier: The raw project identifier

        Returns:
            Normalized identifier suitable for env var lookup
        """
        return identifier.upper().replace("-", "_").replace(" ", "_")

    @staticmethod
    def _lookup_env_url(env_var_name: str) -> Optional[str]:
        """
        Look up an environment variable and return its value if set.

        Args:
            env_var_name: The environment variable name

        Returns:
            The environment variable value or None if not set
        """
        value = os.getenv(env_var_name)
        if value:
            logger.debug("Found environment variable %s=%s", env_var_name, value)
            return value.strip()
        return None

    def _map_team_document_urls(
        self, project_identifier: Optional[str]
    ) -> Dict[str, str]:
        """
        Map team document URLs based on project identifier and environment variables.

        All environment variables are REQUIRED. If any are missing, raises ValueError.

        Looks up the following REQUIRED environment variables:
        - PROJECT_REPO_{PROJECT_IDENTIFIER}
        - TEAM_CONTRIBUTION_RULES_URL_{PROJECT_IDENTIFIER}
        - ARCHITECTURE_RULES_URL_{PROJECT_IDENTIFIER}

        Note: PRD and ARD URLs should be included in the issue description, not in environment variables.

        Args:
            project_identifier: The normalized project identifier (e.g., "BACKEND")

        Returns:
            Dictionary with mapped URLs (all required):
            - project_repo_url
            - team_contribution_rules_url
            - team_architecture_rules_url

        Raises:
            ValueError: If project_identifier is None or if any required environment variable is missing
        """
        if not project_identifier:
            error_msg = "Project identifier is required but not found in issue summary or labels"
            logger.error(error_msg)
            raise ValueError(error_msg)

        missing_vars = []
        urls = {}

        # Map repository URL (REQUIRED)
        repo_env_var = f"PROJECT_REPO_{project_identifier}"
        repo_url = self._lookup_env_url(repo_env_var)
        if not repo_url:
            missing_vars.append(repo_env_var)
        else:
            urls["project_repo_url"] = repo_url

        # Map team contribution rules URL (REQUIRED)
        contribution_env_var = f"TEAM_CONTRIBUTION_RULES_URL_{project_identifier}"
        contribution_url = self._lookup_env_url(contribution_env_var)
        if not contribution_url:
            missing_vars.append(contribution_env_var)
        else:
            urls["team_contribution_rules_url"] = contribution_url

        # Map architecture rules URL (REQUIRED)
        architecture_env_var = f"ARCHITECTURE_RULES_URL_{project_identifier}"
        architecture_url = self._lookup_env_url(architecture_env_var)
        if not architecture_url:
            missing_vars.append(architecture_env_var)
        else:
            urls["team_architecture_rules_url"] = architecture_url

        # If any required environment variables are missing, raise error
        if missing_vars:
            error_msg = (
                f"Missing required environment variables for project '{project_identifier}': "
                f"{', '.join(missing_vars)}. "
                f"Please set all required environment variables for this project."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(
            "Successfully mapped all URLs for project '%s': repo=%s, contribution=%s, architecture=%s",
            project_identifier,
            bool(urls["project_repo_url"]),
            bool(urls["team_contribution_rules_url"]),
            bool(urls["team_architecture_rules_url"]),
        )

        return urls

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

        # Extract project identifier from summary or labels
        # Returns (normalized_identifier, raw_identifier)
        normalized_identifier, raw_identifier = self._extract_project_identifier(summary, labels)

        # Map team document URLs based on normalized project identifier
        url_mapping = self._map_team_document_urls(normalized_identifier)

        # Determine team_name: use raw_identifier if available, otherwise use project_key
        # raw_identifier is more descriptive (e.g., "backend", "web-front") than project_key (e.g., "PROJ")
        team_name = raw_identifier if raw_identifier else project_key if project_key else None

        logger.debug(
            "Mapped issue %s: project_key=%s, project_identifier=%s, team_name=%s",
            issue_key,
            project_key,
            normalized_identifier,
            team_name,
        )

        return IssueEntity(
            id=jira_issue.get("id", ""),
            key=issue_key,
            project_key=project_key,
            status=status,
            labels=labels,
            summary=summary,
            description=description,
            team_name=team_name,
            project_repo_url=url_mapping["project_repo_url"],
            team_contribution_rules_url=url_mapping["team_contribution_rules_url"],
            team_architecture_rules_url=url_mapping["team_architecture_rules_url"],
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


