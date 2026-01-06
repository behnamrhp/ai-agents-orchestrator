"""
OrchestratorService definition in its own module.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

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

    def _is_selected_for_development(self, status: str) -> bool:
        """
        Check if issue status indicates "Selected for Development".

        Args:
            status: The issue status string

        Returns:
            True if status indicates "Selected for Development", False otherwise
        """
        status_lower = status.lower()
        return "selected" in status_lower and "development" in status_lower

    def _is_to_approve(self, status: str) -> bool:
        """
        Check if issue status indicates "to approve".

        Args:
            status: The issue status string

        Returns:
            True if status indicates "to approve", False otherwise
        """
        status_lower = status.lower()
        return "approve" in status_lower or "to approve" in status_lower

    def _get_role_definition(self, issue: IssueEntity) -> str:
        """
        Get role definition based on issue status.

        Explicitly checks issue status and returns appropriate role:
        - "Selected for Development" → Senior Software Developer
        - "to approve" → Senior Software Architect
        - Other statuses → Development Agent (default)

        Args:
            issue: The issue entity containing status and project information

        Returns:
            Role definition string for the agent
        """
        # Use team_name from issue entity if available, otherwise fall back to project_key
        team_name = issue.team_name or issue.project_key or "the team"

        # Check for "Selected for Development" status
        if self._is_selected_for_development(issue.status):
            logger.debug(
                "Issue %s is in 'Selected for Development' status - assigning Developer role",
                issue.key,
            )
            return (
                f"Role: Senior Software Developer\n"
                f"You are a senior software developer in the {team_name} team. "
                f"Your responsibility is to implement features and fixes according to "
                f"team standards, architecture requirements, and best practices."
            )

        # Check for "to approve" status
        if self._is_to_approve(issue.status):
            logger.debug(
                "Issue %s is in 'to approve' status - assigning Architect role",
                issue.key,
            )
            return (
                f"Role: Senior Software Architect\n"
                f"You are a senior software architect responsible for reviewing and approving "
                f"pull requests. You must ensure that the implementation follows all requirements "
                f"and best practices."
            )

        # Default role for other statuses
        logger.debug(
            "Issue %s is in status '%s' - assigning default Development Agent role",
            issue.key,
            issue.status,
        )
        return (
            f"Role: Development Agent\n"
            f"You are a development agent responsible for implementing features and fixes "
            f"according to team standards and architecture requirements."
        )

    def _get_status_specific_instructions(self, issue: IssueEntity) -> List[str]:
        """
        Get status-specific instructions for the agent based on issue status.

        Explicitly checks issue status and returns appropriate instructions:
        - "Selected for Development" → Developer implementation instructions
        - "to approve" → Architect review instructions
        - Other statuses → Default instructions

        Args:
            issue: The issue entity containing status information

        Returns:
            List of instruction strings
        """
        instructions = []

        # Check for "Selected for Development" status
        if self._is_selected_for_development(issue.status):
            logger.debug(
                "Generating Developer instructions for issue %s",
                issue.key,
            )
            instructions.extend([
                "1. Review the PRD (Product Requirements Document) and ARD (Architecture Requirements Document) "
                "URLs that are mentioned in the issue description above. You MUST access these URLs and read the documents "
                "before proceeding. Use appropriate tools (browser, curl, or MCP tools) to access the PRD and ARD URLs from the issue description.",
                "",
                "2. Implement the feature or fix according to:",
                "   - Product Requirements Document (PRD) - read from URL in issue description",
                "   - Architecture Requirements Document (ARD) - read from URL in issue description",
                "   - Team contribution rules",
                "   - Team architecture rules",
                "   - Software development best practices (clean code, proper resource usage, etc.)",
                "",
                "3. Create a separate branch in the repository for this task. Use a descriptive branch name that includes and based on team contibution rules"
                "the issue key (e.g., 'feature/PROJ-123-add-authentication' or 'fix/PROJ-456-resolve-bug').",
                "",
                "4. Make a Pull Request (PR) in the repository with your implementation. Ensure the PR:",
                "   - Has a clear title and description",
                "   - References the Jira issue key in the description",
                "   - Includes all necessary changes for the task",
                "   - Follows the team's PR guidelines",
                "",
                "5. Once the PR is created, you MUST update the issue status in Jira to 'to approve' using the Jira MCP tools "
                "available to you. This is a required step to mark the task as ready for architecture review.",
            ])

        # Check for "to approve" status
        elif self._is_to_approve(issue.status):
            logger.debug(
                "Generating Architect review instructions for issue %s",
                issue.key,
            )
            instructions.extend([
                "1. Review the Pull Request (PR) that was created for this issue. Ensure it is properly linked to the issue.",
                "",
                "2. Thoroughly review the code changes in the git repository. Examine:",
                "   - All files changed in the PR",
                "   - Code quality and structure",
                "   - Implementation approach and patterns",
                "   - Test coverage and quality",
                "",
                "3. Add review comments directly in the git repository (PR comments) for any issues, suggestions, or questions. "
                "Be specific and constructive in your feedback.",
                "",
                "4. Verify that the PR implementation follows all requirements:",
                "   - Product Requirements Document (PRD) - all requirements are met (read PRD from URL in issue description)",
                "   - Architecture Requirements Document (ARD) - architecture guidelines are followed (read ARD from URL in issue description)",
                "   - Team contribution rules - code style and contribution standards are adhered to",
                "   - Team architecture rules - architectural patterns and principles are respected",
                "",
                "5. Ensure the PR demonstrates best practices of software development:",
                "   - Clean code principles (readability, maintainability, SOLID principles)",
                "   - Proper resource usage (memory, CPU, network, database queries)",
                "   - Error handling and edge cases are properly addressed",
                "   - Code is well-tested and documented",
                "   - Security best practices are followed",
                "",
                "6. Based on your review:",
                "   - If the PR is APPROVED: Update the issue status in Jira to 'to approve by human' using the Jira MCP tools.",
                "   - If the PR is NOT APPROVED: Update the issue status in Jira to 'selected for development' using the Jira MCP tools. "
                "This will send the task back to the developer for revisions based on your review comments.",
                "",
                "7. IMPORTANT: You MUST update the Jira issue status using MCP Jira tools after completing your review, "
                "regardless of whether you approve or reject the PR.",
            ])

        # Default instructions for other statuses
        else:
            logger.debug(
                "Generating default instructions for issue %s with status '%s'",
                issue.key,
                issue.status,
            )
            instructions.extend([
                "1. Please review the PRD (Product Requirements Document) and ARD (Architecture Requirements Document) "
                "URLs that are mentioned in the issue description above. You MUST access these URLs and read the documents "
                "before proceeding. Use appropriate tools (browser, curl, or MCP tools) to access the PRD and ARD URLs from the issue description.",
                "",
                "2. Work on the issue according to team standards and architecture requirements.",
            ])

        return instructions

    def build_agent_prompt(self, issue: IssueEntity, base_prompt: str) -> str:
        """
        Build a comprehensive prompt for the agent based on issue data and status.

        This method constructs a detailed instruction message that includes:
        - Role definition based on issue status (Developer or Architect)
        - The base prompt/instruction
        - Issue metadata (key, project, status, labels)
        - Issue summary and description (which includes PRD and ARD references)
        - Contextual URLs (repository, contribution rules, architecture rules)
        - Status-specific instructions

        Args:
            issue: The domain IssueEntity containing all issue information
            base_prompt: The base instruction/prompt for the agent

        Returns:
            A formatted prompt string ready to send to the LLM repository
        """
        # Get role definition based on status
        role_definition = self._get_role_definition(issue)

        # Use description as-is - PRD and ARD URLs should be included in the issue description
        full_description = issue.description or "(no description provided)"

        # Get status-specific instructions
        status_instructions = self._get_status_specific_instructions(issue)

        # Get team name for display (use team_name from issue, fallback to project_key)
        team_name = issue.team_name or issue.project_key or "the team"

        # Build the complete prompt
        lines = [
            role_definition,
            "",
            base_prompt,
            "",
            "=== Issue Information ===",
            f"Issue key: {issue.key}",
            f"Project key: {issue.project_key}",
            f"Team: {team_name}",
            f"Status: {issue.status}",
            f"Labels: {', '.join(issue.labels) if issue.labels else '(none)'}",
            "",
            f"Summary: {issue.summary}",
            "",
            "Description:",
            full_description,
            "",
            "=== Additional Context ===",
            f"Repository URL: {issue.project_repo_url}",
            f"Team contribution rules URL: {issue.team_contribution_rules_url}",
            f"Architecture rules URL: {issue.team_architecture_rules_url}",
            "",
            "=== Important Note ===",
            "The issue description above may contain PRD (Product Requirements Document) and ARD (Architecture Requirements Document) URLs.",
            "You MUST read and review these documents from the URLs provided in the issue description before proceeding.",
            "Look for PRD and ARD URLs in the description and access them to understand the requirements.",
            "",
            "=== Important Instructions ===",
        ]
        lines.extend(status_instructions)

        # Add URL checking instructions if URLs are available
        url_instructions = self._get_url_checking_instructions(issue)
        if url_instructions:
            lines.append("")
            lines.append("=== Required URL Checks ===")
            lines.extend(url_instructions)

        return "\n".join(lines)

    def _get_url_checking_instructions(self, issue: IssueEntity) -> List[str]:
        """
        Get instructions for checking required URLs.

        Forces the AI agent to check all required URLs before proceeding with work.
        All URLs are required and must be checked.

        Args:
            issue: The issue entity containing URL information

        Returns:
            List of instruction strings for checking URLs
        """
        instructions = []
        urls_to_check = [
            ("Repository URL", issue.project_repo_url, "repository codebase and structure"),
            ("Team contribution rules URL", issue.team_contribution_rules_url, "team contribution guidelines and standards"),
            ("Architecture rules URL", issue.team_architecture_rules_url, "architecture guidelines and patterns"),
        ]

        instructions.append("You MUST check and review ALL of the following URLs before proceeding:")
        instructions.append("")
        for url_name, url_value, description in urls_to_check:
            instructions.append(f"- {url_name}: {url_value}")
            instructions.append(f"  Review this URL to understand the {description}.")
        instructions.append("")
        instructions.append("Additionally, you MUST check the issue description above for PRD (Product Requirements Document) and ARD (Architecture Requirements Document) URLs.")
        instructions.append("If PRD or ARD URLs are mentioned in the issue description, you MUST access and read those documents as well.")
        instructions.append("")
        instructions.append("These URLs and documents contain critical information that you must follow when working on this issue.")
        instructions.append("Use appropriate tools (browser, curl, or MCP tools) to access and review these resources.")
        instructions.append("Do not proceed with implementation or review until you have checked ALL required URLs and documents.")

        return instructions

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
        logger.info("Handling issue created event for issue %s (status: %s)", issue.key, issue.status)

        # Map DTO to domain Issue (already done - event.issue is IssueEntity)
        # Delegate to assignAgent with status-appropriate base prompt
        base_prompt = self._get_base_prompt_for_status(issue.status)
        self.assign_agent(issue=issue, prompt=base_prompt)

        logger.info("Successfully assigned agent for created issue %s", issue.key)

    def handle_issue_updated(self, event: IssueEventDTO) -> None:
        """
        Handle an updated issue event.

        Per the sequence diagram:
        1. Apply domain rules (status/label checks, etc.)
        2. Delegate to assignAgent(domainIssue)

        Domain rules applied:
        - Process issues in "Selected for Development" status
        - Process issues in "to approve" status (for architecture review)
        - Skip issues in terminal states

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

        # Domain rules passed - delegate to assignAgent with status-appropriate base prompt
        base_prompt = self._get_base_prompt_for_status(issue.status)
        self.assign_agent(issue=issue, prompt=base_prompt)

        logger.info("Successfully assigned agent for updated issue %s", issue.key)

    def _get_base_prompt_for_status(self, status: str) -> str:
        """
        Get base prompt based on issue status.

        Args:
            status: The issue status

        Returns:
            Base prompt string appropriate for the status
        """
        status_lower = status.lower()

        if "selected" in status_lower and "development" in status_lower:
            return "Handle this Jira issue that has been selected for development. Implement the required changes according to all specifications and requirements."

        if "approve" in status_lower or "to approve" in status_lower:
            return "Review and approve the Pull Request for this Jira issue. Ensure it meets all requirements and best practices."

        return "Please review and work on this Jira issue."

    def _should_process_issue(self, issue: IssueEntity) -> bool:
        """
        Apply domain rules to determine if an issue should be processed.

        Explicitly checks issue status and applies domain rules:
        - Process issues in "Selected for Development" status (Developer role)
        - Process issues in "to approve" status (Architect role for review)
        - Skip issues in terminal states ("done", "closed", "resolved", "cancelled")
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
            logger.info(
                "Issue %s is in terminal state '%s' - skipping processing",
                issue.key,
                issue.status,
            )
            return False

        # Process "Selected for Development" status (assign Developer role)
        if self._is_selected_for_development(issue.status):
            logger.info(
                "Issue %s is in 'Selected for Development' status - will assign Developer role",
                issue.key,
            )
            return True

        # Process "to approve" status (assign Architect role for review)
        if self._is_to_approve(issue.status):
            logger.info(
                "Issue %s is in 'to approve' status - will assign Architect role for review",
                issue.key,
            )
            return True

        # Additional domain rules can be added here:
        # - Label-based filtering (e.g., only process issues with "ai" label)
        # - Project-based filtering
        # - Custom status workflows

        # Default: process other statuses (can be made more restrictive if needed)
        logger.info(
            "Issue %s is in status '%s' - will process with default role",
            issue.key,
            issue.status,
        )
        return True


