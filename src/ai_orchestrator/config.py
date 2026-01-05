"""Configuration management for AI Orchestrator."""

from typing import Optional

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """LLM configuration settings."""

    model_config = SettingsConfigDict(env_prefix="LLM_", case_sensitive=False)

    api_key: SecretStr
    model: str = "anthropic/claude-sonnet-4-5-20250929"
    base_url: Optional[str] = None


class JiraConfig(BaseSettings):
    """Jira configuration for MCP server."""

    model_config = SettingsConfigDict(env_prefix="JIRA_", case_sensitive=False)

    url: str
    username: str
    api_token: SecretStr


class ConfluenceConfig(BaseSettings):
    """Confluence configuration for MCP server."""

    model_config = SettingsConfigDict(env_prefix="CONFLUENCE_", case_sensitive=False)

    url: str
    username: str
    api_token: SecretStr


class MCPConfig(BaseSettings):
    """MCP server configuration."""

    model_config = SettingsConfigDict(env_prefix="MCP_", case_sensitive=False)

    atlassian_command: str = "npx"
    atlassian_args: str = "-y,@sooperset/mcp-atlassian"


class OrchestratorConfig:
    """Main orchestrator configuration."""

    def __init__(self, **kwargs):
        """Initialize configuration from environment variables."""
        self.llm = LLMConfig(**kwargs)
        self.jira = JiraConfig(**kwargs)
        self.confluence = ConfluenceConfig(**kwargs)
        self.mcp = MCPConfig(**kwargs)

    def get_mcp_config(self) -> dict:
        """Get MCP configuration dictionary for OpenHands."""
        # Parse the args string into a list
        # Handle both comma-separated and space-separated formats
        if "," in self.mcp.atlassian_args:
            args = [arg.strip() for arg in self.mcp.atlassian_args.split(",")]
        else:
            args = self.mcp.atlassian_args.split()

        return {
            "mcpServers": {
                "atlassian": {
                    "command": self.mcp.atlassian_command,
                    "args": args,
                    "env": {
                        "JIRA_URL": self.jira.url,
                        "JIRA_USERNAME": self.jira.username,
                        "JIRA_API_TOKEN": self.jira.api_token.get_secret_value(),
                        "CONFLUENCE_URL": self.confluence.url,
                        "CONFLUENCE_USERNAME": self.confluence.username,
                        "CONFLUENCE_API_TOKEN": self.confluence.api_token.get_secret_value(),
                    },
                }
            }
        }

