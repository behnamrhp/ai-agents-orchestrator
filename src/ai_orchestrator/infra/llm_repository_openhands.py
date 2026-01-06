"""
Concrete implementation of the LlmRepository interface for OpenHands.

Supports three modes:
1. Remote OpenHands server - connects to a self-hosted OpenHands instance
2. Local Docker workspace - runs agents in local Docker containers
3. Simple conversation - no sandboxed execution (fallback)

For self-hosted OpenHands:
- Set OPENHANDS_SERVER_URL to your OpenHands server URL
- Set OPENHANDS_API_KEY if authentication is required
"""

from __future__ import annotations

import logging
from typing import Any

from openhands.sdk import Agent, LLM, RemoteConversation
from openhands.sdk.workspace import RemoteWorkspace
from openhands.workspace import DockerWorkspace

from ai_orchestrator.domain.issue_entity import IssueEntity
from ai_orchestrator.domain.repositories import LlmRepository
from ai_orchestrator.infra.config import LlmConfig, OpenHandsConfig

logger = logging.getLogger(__name__)


class OpenHandsLlmRepository(LlmRepository):
    """
    OpenHands-backed implementation of the LlmRepository interface.

    This repository is responsible for triggering an OpenHands agent run
    for a given Jira issue. It does **not** read or return the agent's
    response; the goal is to have the run visible in OpenHands itself.

    Execution modes (in order of priority):
    1. Remote server: If OPENHANDS_SERVER_URL is set, connects to self-hosted OpenHands
    2. Docker workspace: If Docker is available, runs agents in local containers
    3. Simple conversation: Fallback mode without sandboxed execution
    """

    def __init__(
        self,
        llm_config: LlmConfig,
        openhands_config: OpenHandsConfig | None = None,
        client: Any | None = None,
    ) -> None:
        """
        Initialize the repository with LLM configuration.

        Args:
            llm_config: Configuration for the underlying LLM used by OpenHands.
            openhands_config: Optional configuration for workspace/server settings.
            client: Optional pre-configured OpenHands conversation/client.
        """
        self._llm_config = llm_config
        self._openhands_config = openhands_config
        self._workspace: RemoteWorkspace | DockerWorkspace | None = None
        self._conversation: RemoteConversation | Any = None

        if client is not None:
            # Allow injecting a pre-configured OpenHands conversation/client
            self._conversation = client
            logger.info("Using injected OpenHands client for LLM repository")
            return

        # Build LLM from configuration
        llm_kwargs: dict[str, Any] = {
            "model": llm_config.model,
        }
        # Only add api_key if provided (optional - may be configured in OpenHands)
        if llm_config.api_key:
            llm_kwargs["api_key"] = llm_config.api_key
        # Only add base_url if provided (optional - uses provider default)
        if llm_config.base_url:
            llm_kwargs["base_url"] = llm_config.base_url

        llm = LLM(**llm_kwargs)

        # For now we use a basic agent without explicit tools.
        # MCP tools (e.g., Atlassian) are configured via the OpenHands SDK
        # using environment variables and mcpServers config.
        agent = Agent(
            llm=llm,
            tools=[],  # MCP tools are configured via environment variables, not here
        )

        # Mode 1: Remote OpenHands server (self-hosted)
        if openhands_config and openhands_config.server_url:
            self._init_remote_server(agent, openhands_config)
            return

        # Mode 2: Local Docker workspace
        use_docker = openhands_config.use_docker_workspace if openhands_config else True
        if use_docker:
            if self._init_docker_workspace(agent, openhands_config):
                return

        # Mode 3: Simple conversation (fallback)
        self._init_simple_conversation(agent)

    def _init_remote_server(
        self, agent: Agent, openhands_config: OpenHandsConfig
    ) -> None:
        """Initialize connection to a remote OpenHands server."""
        server_url = openhands_config.server_url
        api_key = openhands_config.api_key
        working_dir = openhands_config.working_dir

        logger.info("Connecting to remote OpenHands server at %s", server_url)

        try:
            # Create RemoteWorkspace to connect to the OpenHands server
            workspace = RemoteWorkspace(
                host=server_url,
                api_key=api_key,
                working_dir=working_dir,
            )

            # Create RemoteConversation which uses the workspace
            self._conversation = RemoteConversation(
                agent=agent,
                workspace=workspace,
                visualizer=None,  # No local visualization needed
            )
            self._workspace = workspace

            logger.info(
                "Successfully connected to remote OpenHands server at %s",
                server_url,
            )
        except Exception as e:
            logger.error(
                "Failed to connect to remote OpenHands server at %s: %s",
                server_url,
                e,
                exc_info=True,
            )
            raise RuntimeError(
                f"Cannot connect to OpenHands server at {server_url}: {e}"
            ) from e

    def _init_docker_workspace(
        self, agent: Agent, openhands_config: OpenHandsConfig | None
    ) -> bool:
        """Initialize local Docker workspace. Returns True on success."""
        from openhands.sdk import Conversation

        working_dir = openhands_config.working_dir if openhands_config else "/workspace"

        try:
            logger.info("Initializing Docker workspace for agent execution")
            workspace = DockerWorkspace(working_dir=working_dir)
            self._conversation = Conversation(agent=agent, workspace=workspace)
            self._workspace = workspace
            logger.info("Initialized OpenHands with Docker workspace")
            return True
        except Exception as e:
            logger.warning(
                "Failed to initialize Docker workspace: %s. "
                "Falling back to simple conversation mode.",
                e,
            )
            return False

    def _init_simple_conversation(self, agent: Agent) -> None:
        """Initialize simple conversation mode without sandboxed execution."""
        from openhands.sdk import Conversation

        self._conversation = Conversation(agent=agent)
        self._workspace = None
        logger.info("Initialized OpenHands in simple conversation mode (no sandbox)")

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


