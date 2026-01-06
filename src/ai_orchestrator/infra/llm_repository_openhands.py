"""
Concrete implementation of the LlmRepository interface for OpenHands.

All real communication with OpenHands and Atlassian MCP will be added later.
"""

from __future__ import annotations

import logging
from typing import Any

from openhands.sdk import Agent, Conversation, LLM

from ai_orchestrator.domain.issue_entity import IssueEntity
from ai_orchestrator.domain.repositories import LlmRepository
from ai_orchestrator.infra.config import LlmConfig

logger = logging.getLogger(__name__)


class OpenHandsLlmRepository(LlmRepository):
    """
    OpenHands-backed implementation of the LlmRepository interface.

    This repository is responsible for triggering an OpenHands agent run
    for a given Jira issue. It does **not** read or return the agent's
    response; the goal is to have the run visible in OpenHands itself.
    """

    def __init__(self, llm_config: LlmConfig, client: Any | None = None) -> None:
        """
        Initialize the repository with LLM configuration.

        Args:
            llm_config: Configuration for the underlying LLM used by OpenHands.
            client: Optional pre-configured OpenHands conversation/client.
        """
        self._llm_config = llm_config

        if client is not None:
            # Allow injecting a pre-configured OpenHands conversation/client
            self._conversation: Conversation = client
            logger.info("Using injected OpenHands client for LLM repository")
            return

        # Build LLM from configuration
        llm_kwargs: dict[str, Any] = {
            "model": llm_config.model,
            "api_key": llm_config.api_key,
        }
        if llm_config.base_url:
            llm_kwargs["base_url"] = llm_config.base_url

        llm = LLM(**llm_kwargs)

        # For now we use a basic agent without explicit tools.
        # MCP tools (e.g., Atlassian) are configured via the OpenHands SDK
        # using environment variables and mcpServers config.
        # Tools will be automatically discovered from MCP servers configured via environment variables.
        agent = Agent(
            llm=llm,
            tools=[],  # MCP tools are configured via environment variables, not here
        )

        self._conversation = Conversation(agent=agent)
        logger.info("Initialized OpenHands Conversation for LLM repository")

    def check_mcp_connection(self, provider: str) -> bool:
        """
        Check if the specified MCP provider is connected in OpenHands.

        Note:
            A full MCP health check requires deeper OpenHands integration.
            For now we log the intent and optimistically return True so that
            startup can proceed while relying on OpenHands' own error handling.
        """
        logger.info("Checking MCP connection for provider '%s' (stubbed as True)", provider)
        return True

    def connect_mcp(self, provider: str) -> None:
        """
        Establish a connection for the specified MCP provider.

        Note:
            MCP servers (like Atlassian) are configured via environment
            variables and mcpServers config in OpenHands. This method is
            provided for API symmetry and future extension.
        """
        logger.info("Ensuring MCP provider '%s' is configured (no-op stub)", provider)

    def assign_agent(self, issue: IssueEntity, prompt: str) -> None:
        """
        Assign an agent in OpenHands for the given issue.

        This method receives a fully-formed prompt (built by the domain layer)
        and sends it to an OpenHands Conversation to trigger an agent run.
        The response is not captured; the run is observable via OpenHands itself.

        Args:
            issue: The issue entity (kept for logging purposes)
            prompt: The complete prompt string built by OrchestratorService
        """
        logger.info(
            "Starting OpenHands agent run for issue %s with model '%s'",
            issue.key,
            self._llm_config.model,
        )

        # Send the prompt (already built by domain layer) to the agent and run the conversation.
        # We deliberately ignore the return value; the run is for OpenHands UI/logs.
        self._conversation.send_message(prompt)
        self._conversation.run()

        logger.info("OpenHands agent run completed for issue %s", issue.key)


