"""
McpStartupService definition in its own module.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .repositories import LlmRepository

logger = logging.getLogger(__name__)


@dataclass
class McpStartupService:
    """
    Ensures required MCP providers (e.g., Atlassian) are connected during startup.

    This service follows the sequence diagram: it checks if MCP is connected,
    and if not, establishes the connection before the application starts serving requests.
    """

    llm_repository: LlmRepository
    provider_name: str = "atlassian"

    def on_startup(self) -> None:
        """
        Startup hook that checks and establishes MCP connections as needed.

        Per the sequence diagram:
        1. Check if MCP provider is connected via llm_repository
        2. If not connected, connect it
        3. If already connected, skip (log "already connected")
        """
        logger.info("Checking MCP connection for provider '%s'", self.provider_name)

        # Check connection status via LLM repository
        is_connected = self.llm_repository.check_mcp_connection(self.provider_name)

        if is_connected:
            logger.info(
                "MCP provider '%s' is already connected. Skipping connection step.",
                self.provider_name,
            )
            return

        # MCP not connected - establish connection
        logger.info(
            "MCP provider '%s' is not connected. Establishing connection...",
            self.provider_name,
        )

        try:
            self.llm_repository.connect_mcp(self.provider_name)
            logger.info(
                "Successfully connected MCP provider '%s'",
                self.provider_name,
            )
        except Exception as e:
            logger.error(
                "Failed to connect MCP provider '%s': %s",
                self.provider_name,
                e,
                exc_info=True,
            )
            # Re-raise to allow startup to fail if MCP connection is critical
            raise


