"""
Concrete implementation of the LlmRepository interface for OpenHands.

Supports three modes:
1. Remote OpenHands server - connects to a self-hosted OpenHands instance
2. Local Docker workspace - runs agents in local Docker containers
3. Simple conversation - no sandboxed execution (fallback)

For self-hosted OpenHands:
- Set OPENHANDS_SERVER_URL to your OpenHands server URL
- Set OPENHANDS_API_KEY if authentication is required

MCP Server Configuration:
- MCP servers (like Atlassian) are configured via environment variables
- Required env vars: JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
- Optional env vars: CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN
- MCP_ATLASSIAN_COMMAND and MCP_ATLASSIAN_ARGS configure the MCP server command
"""

from __future__ import annotations

import logging
import os
from typing import Any

from openhands.sdk import Agent, LLM, RemoteConversation
from openhands.sdk.workspace import RemoteWorkspace
from openhands.workspace import DockerWorkspace

from ai_orchestrator.domain.issue_entity import IssueEntity
from ai_orchestrator.domain.repositories import LlmRepository
from ai_orchestrator.infra.config import LlmConfig, McpConfig, OpenHandsConfig

logger = logging.getLogger(__name__)

# MCP provider configuration mapping
MCP_PROVIDER_ENV_VARS: dict[str, list[str]] = {
    "atlassian": [
        "JIRA_URL",
        "JIRA_USERNAME",
        "JIRA_API_TOKEN",
    ],
}

MCP_PROVIDER_OPTIONAL_ENV_VARS: dict[str, list[str]] = {
    "atlassian": [
        "JIRA_USERNAME",  # Optional for PAT auth, but recommended
        "CONFLUENCE_URL",
        "CONFLUENCE_USERNAME",
        "CONFLUENCE_API_TOKEN",
    ],
}


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
        mcp_config: McpConfig | None = None,
        client: Any | None = None,
    ) -> None:
        """
        Initialize the repository with LLM configuration.

        Args:
            llm_config: Configuration for the underlying LLM used by OpenHands.
            openhands_config: Optional configuration for workspace/server settings.
            mcp_config: Optional configuration for MCP server settings.
            client: Optional pre-configured OpenHands conversation/client.
        """
        self._llm_config = llm_config
        self._openhands_config = openhands_config
        self._mcp_config = mcp_config
        self._workspace: RemoteWorkspace | DockerWorkspace | None = None
        self._conversation: RemoteConversation | Any = None
        self._mcp_connected: dict[str, bool] = {}

        # Validate LLM configuration early
        self._validate_llm_config()

        if client is not None:
            # Allow injecting a pre-configured OpenHands conversation/client
            self._conversation = client
            logger.info("Using injected OpenHands client for LLM repository")
            return

        # Build LLM from configuration
        # OpenHands SDK uses LiteLLM under the hood, which accepts:
        # - model: The model identifier
        # - api_key: API key for authentication
        # - base_url: Custom API endpoint (also known as api_base in LiteLLM)
        llm_kwargs: dict[str, Any] = {
            "model": llm_config.model,
        }
        # Only add api_key if provided (optional - may be configured in OpenHands)
        if llm_config.api_key:
            llm_kwargs["api_key"] = llm_config.api_key
            logger.info("LLM API key configured for model '%s'", llm_config.model)
        else:
            logger.warning(
                "LLM API key not provided. This may cause authentication errors. "
                "Set LLM_API_KEY environment variable."
            )
        # Only add base_url if provided (optional - uses provider default)
        # According to OpenHands documentation, LLM_BASE_URL should be set as environment variable
        # OpenHands SDK reads from environment variables for LLM configuration
        # We also pass it as a parameter for direct SDK usage (LiteLLM uses 'api_base')
        if llm_config.base_url:
            # Set as environment variable (primary method - OpenHands SDK reads this)
            os.environ["LLM_BASE_URL"] = llm_config.base_url
            # Also pass as parameter for direct SDK initialization
            # LiteLLM (used by OpenHands) accepts 'api_base' parameter
            llm_kwargs["api_base"] = llm_config.base_url
            logger.info("Using custom LLM base URL: %s (set as LLM_BASE_URL env var and api_base parameter)", llm_config.base_url)
        else:
            logger.debug("Using default LLM base URL for model '%s'", llm_config.model)

        try:
            llm = LLM(**llm_kwargs)
            logger.info("LLM initialized successfully with model '%s'", llm_config.model)
        except Exception as e:
            logger.error(
                "Failed to initialize LLM with model '%s': %s. "
                "Check LLM_API_KEY and LLM_MODEL environment variables.",
                llm_config.model,
                e,
                exc_info=True,
            )
            raise RuntimeError(
                f"Cannot initialize LLM: {e}. "
                "Please check LLM_API_KEY and LLM_MODEL configuration."
            ) from e

        # Build MCP servers configuration if available
        mcp_servers = self._build_mcp_servers_config()

        # Create agent with LLM and optional MCP servers
        agent_kwargs: dict[str, Any] = {
            "llm": llm,
            "tools": [],  # Standard tools are empty; MCP provides tools dynamically
        }
        if mcp_servers:
            agent_kwargs["mcp_servers"] = mcp_servers
            logger.info("Configured agent with MCP servers: %s", list(mcp_servers.keys()))

        agent = Agent(**agent_kwargs)

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

    def _validate_llm_config(self) -> None:
        """
        Validate LLM configuration and log warnings for missing values.
        
        Note: API key is optional in config (may be configured elsewhere),
        but will cause authentication errors if not provided.
        """
        if not self._llm_config.api_key:
            logger.warning(
                "LLM_API_KEY is not set. This will cause authentication errors. "
                "Please set the LLM_API_KEY environment variable with a valid API key. "
                "For Deepseek, get your API key from https://platform.deepseek.com/"
            )
        elif not self._llm_config.api_key.strip():
            logger.warning(
                "LLM_API_KEY is set but empty. "
                "Please provide a valid API key in the LLM_API_KEY environment variable."
            )
        
        # Check if model name looks valid
        if not self._llm_config.model or not self._llm_config.model.strip():
            logger.warning(
                "LLM_MODEL is not set or empty. Using default 'deepseek'. "
                "For Deepseek, you may need to use 'deepseek/deepseek-chat' format. "
                "Set LLM_MODEL environment variable to override."
            )
        
        logger.debug(
            "LLM configuration: model='%s', api_key_present=%s",
            self._llm_config.model,
            bool(self._llm_config.api_key),
        )

    def _build_mcp_servers_config(self) -> dict[str, Any] | None:
        """
        Build MCP servers configuration from environment variables and config.

        Returns:
            Dictionary with mcpServers configuration format, or None if not configured.
        """
        if not self._mcp_config:
            logger.debug("No MCP config provided, skipping MCP servers configuration")
            return None

        # Build Atlassian MCP server config from environment variables
        mcp_env = {}
        for env_var in MCP_PROVIDER_ENV_VARS.get("atlassian", []):
            value = os.environ.get(env_var)
            if value:
                mcp_env[env_var] = value

        # Add optional env vars if present
        for env_var in MCP_PROVIDER_OPTIONAL_ENV_VARS.get("atlassian", []):
            value = os.environ.get(env_var)
            if value:
                mcp_env[env_var] = value

        # If no environment variables are set, don't configure MCP
        if not mcp_env:
            logger.warning(
                "MCP config provided but no Atlassian environment variables set. "
                "Required: %s",
                MCP_PROVIDER_ENV_VARS.get("atlassian", []),
            )
            return None

        # Parse args from config (comma-separated string to list)
        args = []
        if self._mcp_config.args:
            args = [arg.strip() for arg in self._mcp_config.args.split(",") if arg.strip()]

        mcp_servers = {
            "atlassian": {
                "command": self._mcp_config.command,
                "args": args,
                "env": mcp_env,
            }
        }

        logger.debug("Built MCP servers config: %s", list(mcp_servers.keys()))
        return mcp_servers

    def _check_mcp_env_vars(self, provider: str) -> tuple[bool, list[str]]:
        """
        Check if required environment variables for an MCP provider are set.

        Args:
            provider: The MCP provider name (e.g., "atlassian")

        Returns:
            Tuple of (all_required_set, missing_vars)
        """
        required_vars = MCP_PROVIDER_ENV_VARS.get(provider, [])
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        return len(missing_vars) == 0, missing_vars

    def check_mcp_connection(self, provider: str) -> bool:
        """
        Check if the specified MCP provider is connected in OpenHands.

        This method verifies:
        1. Required environment variables are set for the provider
        2. MCP config is available
        3. The provider has been marked as connected

        Note:
            Full MCP health check (verifying the MCP server process is running
            and responsive) would require deeper integration. This check verifies
            the configuration is in place.

        Args:
            provider: The MCP provider name (e.g., "atlassian")

        Returns:
            True if the provider is properly configured and marked as connected
        """
        logger.info("Checking MCP connection for provider '%s'", provider)

        # Check if already marked as connected
        if self._mcp_connected.get(provider):
            logger.info("MCP provider '%s' is already marked as connected", provider)
            return True

        # Check environment variables
        env_vars_ok, missing_vars = self._check_mcp_env_vars(provider)
        if not env_vars_ok:
            logger.warning(
                "MCP provider '%s' missing required environment variables: %s",
                provider,
                missing_vars,
            )
            return False

        # Check MCP config
        if not self._mcp_config:
            logger.warning(
                "MCP provider '%s' has environment variables but no MCP config",
                provider,
            )
            return False

        logger.info(
            "MCP provider '%s' configuration verified (env vars and config present)",
            provider,
        )
        return True

    def connect_mcp(self, provider: str) -> None:
        """
        Establish a connection for the specified MCP provider.

        MCP servers (like Atlassian) are configured via environment variables
        and mcpServers config in OpenHands. This method:
        1. Verifies required environment variables are set
        2. Marks the provider as connected for subsequent checks

        Note:
            The actual MCP server connection is established lazily by OpenHands
            when the agent needs to use MCP tools. This method primarily validates
            configuration and marks the provider as ready.

        Args:
            provider: The MCP provider name (e.g., "atlassian")

        Raises:
            RuntimeError: If required environment variables are missing
        """
        logger.info("Connecting MCP provider '%s'", provider)

        # Verify environment variables
        env_vars_ok, missing_vars = self._check_mcp_env_vars(provider)
        if not env_vars_ok:
            error_msg = (
                f"Cannot connect MCP provider '{provider}': "
                f"missing required environment variables: {missing_vars}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Verify MCP config
        if not self._mcp_config:
            error_msg = (
                f"Cannot connect MCP provider '{provider}': "
                f"MCP configuration not provided"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Mark as connected
        self._mcp_connected[provider] = True
        logger.info(
            "MCP provider '%s' marked as connected. "
            "Command: %s, Args: %s",
            provider,
            self._mcp_config.command,
            self._mcp_config.args,
        )

    def assign_agent(self, issue: IssueEntity, prompt: str) -> None:
        """
        Assign an agent in OpenHands for the given issue.

        This method receives a fully-formed prompt (built by the domain layer)
        and sends it to an OpenHands Conversation to trigger an agent run.
        The response is not captured; the run is observable via OpenHands itself.

        Args:
            issue: The issue entity (kept for logging purposes)
            prompt: The complete prompt string built by OrchestratorService

        Raises:
            RuntimeError: If the conversation is not initialized or agent run fails
        """
        if self._conversation is None:
            error_msg = "Cannot assign agent: OpenHands conversation not initialized"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(
            "Starting OpenHands agent run for issue %s with model '%s'",
            issue.key,
            self._llm_config.model,
        )
        logger.debug("Prompt length: %d characters", len(prompt))

        try:
            # Send the prompt (already built by domain layer) to the agent
            self._conversation.send_message(prompt)
            logger.info("Message sent to OpenHands agent for issue %s", issue.key)

            # Run the conversation - this triggers the agent to process the prompt
            self._conversation.run()
            logger.info("OpenHands agent run completed for issue %s", issue.key)

        except Exception as e:
            error_str = str(e)
            error_msg = f"Agent run failed for issue {issue.key}: {error_str}"
            
            # Provide specific guidance for authentication errors
            if "Authentication" in error_str or "AuthenticationError" in error_str:
                logger.error(
                    "LLM Authentication failed for issue %s. "
                    "Please check:\n"
                    "  1. LLM_API_KEY is set correctly in environment variables\n"
                    "  2. The API key is valid and not expired\n"
                    "  3. The API key has proper permissions for the model '%s'\n"
                    "  4. For Deepseek: Ensure you're using a valid Deepseek API key\n"
                    "Error: %s",
                    issue.key,
                    self._llm_config.model,
                    error_str,
                    exc_info=True,
                )
                raise RuntimeError(
                    f"LLM Authentication failed for issue {issue.key}. "
                    f"Please verify LLM_API_KEY is set correctly and valid. "
                    f"Model: {self._llm_config.model}, Error: {error_str}"
                ) from e
            
            logger.error(
                "OpenHands agent run failed for issue %s: %s",
                issue.key,
                error_str,
                exc_info=True,
            )
            raise RuntimeError(error_msg) from e


