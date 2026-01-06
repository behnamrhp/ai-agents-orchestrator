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
    )

    api_key: str = Field(..., description="API key for the underlying LLM provider")
    model: str = Field(
        default="deepseek",
        description="LLM model identifier used by OpenHands (e.g., deepseek, anthropic/claude-3-5-sonnet)",
    )
    base_url: str = Field(
        ...,
        description="Base URL for LLM endpoints",
    )


class JiraConfig(BaseSettings):
    """Jira configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="JIRA_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
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
    )

    command: str = Field(..., description="Command to run MCP server (e.g., npx)")
    args: str = Field(..., description="Arguments for MCP server (e.g., -y,@sooperset/mcp-atlassian)")


class AppConfig(BaseSettings):
    """Application-wide configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    llm: LlmConfig = Field(default_factory=LlmConfig)
    jira: JiraConfig = Field(default_factory=JiraConfig)
    webhook: WebhookConfig = Field(default_factory=WebhookConfig)
    confluence: ConfluenceConfig = Field(default_factory=ConfluenceConfig)
    mcp: McpConfig = Field(default_factory=McpConfig)

