"""
Configuration management using pydantic-settings.

Loads configuration from environment variables with validation.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
        description="Whether to register webhooks on startup (set to false to skip registration)",
    )


class AppConfig(BaseSettings):
    """Application-wide configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    jira: JiraConfig = Field(default_factory=JiraConfig)
    webhook: WebhookConfig = Field(default_factory=WebhookConfig)

