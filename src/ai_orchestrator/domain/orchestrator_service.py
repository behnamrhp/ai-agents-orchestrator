"""
OrchestratorService definition in its own module.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .models import IssueEntity, IssueEventDTO
from .repositories import LlmRepository

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorService:
    """
    Coordinates domain rules and interactions with the LLM repository.

    Core business logic will be implemented later.
    """

    llm_repository: LlmRepository

    def build_agent_prompt(self, issue: IssueEntity, base_prompt: str) -> str:
        """
        Build a comprehensive prompt for the agent based on issue data.

        This method constructs a detailed instruction message that includes:
        - The base prompt/instruction
        - Issue metadata (key, project, status, labels)
        - Issue summary and description (which includes PRD and ARD references)
        - Contextual URLs (repository, contribution rules, architecture rules)
        - Instructions to check PRD and ARD from the description
        - Instructions to update the issue status to "to approve" using Jira MCP

        Args:
            issue: The domain IssueEntity containing all issue information
            base_prompt: The base instruction/prompt for the agent

        Returns:
            A formatted prompt string ready to send to the LLM repository
        """
        # Build description section, including PRD and ARD references if present
        description_parts = [issue.description or "(no description provided)"]

        # Add PRD and ARD URLs to description if they exist
        if issue.prd_url:
            description_parts.append(f"\nPRD URL: {issue.prd_url}")
        if issue.ard_url:
            description_parts.append(f"\nARD URL: {issue.ard_url}")

        full_description = "\n".join(description_parts)

        # Build the complete prompt
        lines = [
            base_prompt,
            "",
            "=== Issue Information ===",
            f"Issue key: {issue.key}",
            f"Project key: {issue.project_key}",
            f"Status: {issue.status}",
            f"Labels: {', '.join(issue.labels) if issue.labels else '(none)'}",
            "",
            f"Summary: {issue.summary}",
            "",
            "Description:",
            full_description,
            "",
            "=== Additional Context ===",
            f"Repository URL: {issue.project_repo_url or '(not set)'}",
            f"Team contribution rules URL: {issue.team_contribution_rules_url or '(not set)'}",
            f"Architecture rules URL: {issue.team_architecture_rules_url or '(not set)'}",
            "",
            "=== Important Instructions ===",
            "1. Please review the PRD (Product Requirements Document) and ARD (Architecture Requirements Document) "
            "that are referenced in the issue description above. Use the Jira MCP tools to access these documents "
            "if they are linked.",
            "",
            "2. Once you have completed the work for this issue, you must update the issue status to 'to approve' "
            "using the Jira MCP tools available to you. This is a required step to mark the task as ready for review.",
        ]

        return "\n".join(lines)

    def assign_agent(self, issue: IssueEntity, prompt: str) -> None:
        """
        Assign an agent for the given issue using the provided prompt.

        Builds a comprehensive prompt using domain logic and delegates to
        the LLM repository to trigger the agent run.
        """
        # Build the full prompt using domain logic
        full_prompt = self.build_agent_prompt(issue=issue, base_prompt=prompt)

        # Delegate to the repository to trigger the agent run
        self.llm_repository.assign_agent(issue=issue, prompt=full_prompt)

    def handle_issue_created(self, event: IssueEventDTO) -> None:
        """
        Handle a newly created issue event.

        Per the sequence diagram:
        1. Map DTO → domain Issue (already done via event.issue)
        2. Delegate to assignAgent(domainIssue)

        Args:
            event: The issue created event DTO
        """
        issue = event.issue
        logger.info("Handling issue created event for issue %s", issue.key)

        # Map DTO to domain Issue (already done - event.issue is IssueEntity)
        # Delegate to assignAgent
        base_prompt = "Please review and work on this newly created Jira issue."
        self.assign_agent(issue=issue, prompt=base_prompt)

        logger.info("Successfully assigned agent for created issue %s", issue.key)

    def handle_issue_updated(self, event: IssueEventDTO) -> None:
        """
        Handle an updated issue event.

        Per the sequence diagram:
        1. Apply domain rules (status/label checks, etc.)
        2. Delegate to assignAgent(domainIssue)

        Domain rules applied:
        - Only process issues that are not already in "to approve" or "done" status
        - Only process issues with certain labels (if configured)
        - Skip if issue is in a terminal state

        Args:
            event: The issue updated event DTO
        """
        issue = event.issue
        logger.info("Handling issue updated event for issue %s (status: %s)", issue.key, issue.status)

        # Apply domain rules: status/label checks
        if not self._should_process_issue(issue):
            logger.info(
                "Skipping agent assignment for issue %s due to domain rules (status: %s)",
                issue.key,
                issue.status,
            )
            return

        # Domain rules passed - delegate to assignAgent
        base_prompt = "Please review and work on this updated Jira issue."
        self.assign_agent(issue=issue, prompt=base_prompt)

        logger.info("Successfully assigned agent for updated issue %s", issue.key)

    def _should_process_issue(self, issue: IssueEntity) -> bool:
        """
        Apply domain rules to determine if an issue should be processed.

        Rules:
        - Skip issues in terminal states ("done", "closed", "resolved")
        - Skip issues already in "to approve" status (work already completed)
        - Can be extended with label-based filtering

        Args:
            issue: The issue to check

        Returns:
            True if the issue should be processed, False otherwise
        """
        # Normalize status for comparison
        status_lower = issue.status.lower()

        # Skip terminal states
        terminal_states = {"done", "closed", "resolved", "cancelled"}
        if status_lower in terminal_states:
            logger.debug(
                "Issue %s is in terminal state '%s' - skipping",
                issue.key,
                issue.status,
            )
            return False

        # Skip if already in "to approve" status (work completed, waiting for review)
        if "approve" in status_lower or "review" in status_lower:
            logger.debug(
                "Issue %s is already in approval/review state '%s' - skipping",
                issue.key,
                issue.status,
            )
            return False

        # Additional domain rules can be added here:
        # - Label-based filtering
        # - Project-based filtering
        # - Custom status workflows

        return True


