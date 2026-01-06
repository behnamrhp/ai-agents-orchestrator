"""
Configuration management using pydantic-settings.

Loads configuration from environment variables with validation.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LlmConfig(BaseSettings):
    """LLM configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra environment variables that don't match LLM_ prefix
    )

    api_key: str | None = Field(
        default=None,
        description="API key for the underlying LLM provider (optional, may be configured in OpenHands)",
    )
    model: str = Field(
        default="deepseek",
        description="LLM model identifier used by OpenHands (e.g., deepseek, anthropic/claude-3-5-sonnet)",
    )
    base_url: str | None = Field(
        default=None,
        description="Base URL for LLM endpoints (optional, uses provider default if not set)",
    )


class JiraConfig(BaseSettings):
    """Jira configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="JIRA_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra environment variables that don't match JIRA_ prefix
    )

    url: str = Field(..., description="Jira instance base URL (e.g., https://your-domain.atlassian.net)")
    username: str = Field(..., description="Jira username/email for API authentication")
    api_token: str = Field(..., description="Jira API token for authentication")


class WebhookConfig(BaseSettings):
    """Webhook registration configuration."""

    model_config = SettingsConfigDict(
        env_prefix="WEBHOOK_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra environment variables that don't match WEBHOOK_ prefix
    )

    base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL where this application is accessible (for webhook callbacks)",
    )
    enabled: bool = Field(
        default=True,
        description="Whether to register webhooks on startup",
    )


class ConfluenceConfig(BaseSettings):
    """Confluence configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="CONFLUENCE_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra environment variables that don't match CONFLUENCE_ prefix
    )

    url: str = Field(..., description="Confluence instance base URL")
    username: str = Field(..., description="Confluence username for API authentication")
    api_token: str = Field(..., description="Confluence API token for authentication")


class McpConfig(BaseSettings):
    """MCP server configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="MCP_ATLASSIAN_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra environment variables that don't match MCP_ATLASSIAN_ prefix
    )

    command: str = Field(..., description="Command to run MCP server (e.g., npx)")
    args: str = Field(..., description="Arguments for MCP server (e.g., -y,@sooperset/mcp-atlassian)")


class OpenHandsConfig(BaseSettings):
    """OpenHands configuration for connecting to a self-hosted OpenHands server.

    Supports multiple execution modes (in order of priority):
    1. Remote server: If SERVER_URL is set, connects to self-hosted OpenHands
    2. Docker workspace: Runs agents in local Docker containers
    3. Simple conversation: Fallback mode without sandboxed execution

    For self-hosted OpenHands:
    - Set OPENHANDS_SERVER_URL to your OpenHands server URL (e.g., http://your-server:3000)
    - Set OPENHANDS_API_KEY if authentication is required
    """

    model_config = SettingsConfigDict(
        env_prefix="OPENHANDS_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra environment variables that don't match OPENHANDS_ prefix
    )

    # Remote server configuration (for self-hosted OpenHands)
    server_url: str | None = Field(
        default=None,
        description="URL of self-hosted OpenHands server (e.g., http://your-server:3000). "
        "If set, connects to remote server. If not set, uses local Docker or simple mode.",
    )
    api_key: str | None = Field(
        default=None,
        description="API key for authenticating with the OpenHands server. "
        "Required if your server requires authentication.",
    )

    # Local workspace configuration
    use_docker_workspace: bool = Field(
        default=True,
        description="Whether to use Docker workspace for local agent execution. "
        "Only used if SERVER_URL is not set. Set to false to use simple conversation mode.",
    )
    working_dir: str = Field(
        default="/workspace",
        description="Working directory for agent execution (both remote and local Docker).",
    )


class AppConfig(BaseSettings):
    """Application-wide configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables (project-specific vars are handled separately)
    )

    llm: LlmConfig = Field(default_factory=LlmConfig)
    jira: JiraConfig = Field(default_factory=JiraConfig)
    webhook: WebhookConfig = Field(default_factory=WebhookConfig)
    confluence: ConfluenceConfig = Field(default_factory=ConfluenceConfig)
    mcp: McpConfig = Field(default_factory=McpConfig)
    openhands: OpenHandsConfig = Field(default_factory=OpenHandsConfig)

