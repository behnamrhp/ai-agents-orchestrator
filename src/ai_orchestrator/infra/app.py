"""
FastAPI application setup for the AI Orchestrator.

Defines the `FastAPIApp` wrapper, registers routes, and provides a
factory for the ASGI app instance.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict

from fastapi import FastAPI
from fastapi import status

from ai_orchestrator.application.controllers import IssueController
from ai_orchestrator.infra.config import WebhookConfig
from ai_orchestrator.infra.di import DI
from ai_orchestrator.infra.jira_client import JiraClient
from ai_orchestrator.infra.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


class FastAPIApp:
    """
    Wrapper around FastAPI to align with the architecture diagram.
    """

    def __init__(
        self,
        issue_controller: IssueController,
        jira_client: JiraClient,
        webhook_config: WebhookConfig,
    ) -> None:
        self._issue_controller = issue_controller
        self._jira_client = jira_client
        self._webhook_config = webhook_config
        self._app = FastAPI()

    @property
    def app(self) -> FastAPI:
        """Expose the underlying FastAPI instance."""
        return self._app

    def register_routes(self) -> None:
        """
        Register HTTP routes for Jira webhooks.

        The handlers delegate directly to the IssueController.
        """

        @self._app.post(
            "/webhooks/jira/issue-created",
            status_code=status.HTTP_200_OK,
        )
        async def issue_created_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
            # TODO: add payload validation / schema
            self._issue_controller.handle_issue_created(payload)
            return {"status": "ok"}

        @self._app.post(
            "/webhooks/jira/issue-updated",
            status_code=status.HTTP_200_OK,
        )
        async def issue_updated_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
            self._issue_controller.handle_issue_updated(payload)
            return {"status": "ok"}

    def register_webhooks(self) -> None:
        """
        Register webhooks with Jira on startup.

        For Jira Cloud: Registers webhooks via REST API.
        For Jira Server/Data Center: Webhook API is not available; logs instructions
        for manual setup and continues startup.
        """
        if not self._webhook_config.enabled:
            logger.info("Webhook registration is disabled via WEBHOOK_ENABLED=false")
            return

        logger.info("Starting webhook registration with Jira...")

        # Test connection first
        if not self._jira_client.test_connection():
            logger.critical(
                "Failed to connect to Jira. Please check JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN.",
                exc_info=True,
            )
            sys.exit(1)

        # Build webhook URLs
        base_url = self._webhook_config.base_url.rstrip("/")
        issue_created_url = f"{base_url}/webhooks/jira/issue-created"
        issue_updated_url = f"{base_url}/webhooks/jira/issue-updated"

        try:
            # Register webhook for issue created events
            self._jira_client.register_webhook(
                webhook_url=issue_created_url,
                events=["jira:issue_created"],
                name="AI Orchestrator - Issue Created",
            )

            # Register webhook for issue updated events
            self._jira_client.register_webhook(
                webhook_url=issue_updated_url,
                events=["jira:issue_updated"],
                name="AI Orchestrator - Issue Updated",
            )

            logger.info("Webhook registration completed successfully")

        except Exception as e:
            # Check if this is a 404 error (webhook API not available on Jira Server)
            is_webhook_api_unavailable = "404" in str(e)

            if is_webhook_api_unavailable:
                logger.warning(
                    "Webhook registration via REST API is not available on Jira Server/Data Center."
                )
                logger.warning(
                    "Please configure webhooks MANUALLY in Jira:\n"
                    "  1. Go to Jira Administration > System > WebHooks\n"
                    "  2. Create a webhook for 'Issue Created' events:\n"
                    f"     URL: {issue_created_url}\n"
                    "     Events: Issue > created\n"
                    "  3. Create a webhook for 'Issue Updated' events:\n"
                    f"     URL: {issue_updated_url}\n"
                    "     Events: Issue > updated\n"
                    "  4. Ensure 'Exclude body' is unchecked (we need the payload)"
                )
                logger.info(
                    "Continuing application startup without automatic webhook registration. "
                    "The app will work once you configure webhooks manually in Jira."
                )
                # Don't exit - continue startup for Jira Server
            else:
                # Other errors should still abort startup
                logger.critical(
                    f"Failed to register webhooks with Jira: {e}. Application startup aborted.",
                    exc_info=True,
                )
                sys.exit(1)

    def start(self) -> FastAPI:
        """
        Initialize the application (webhook registration, routes, and MCP startup) and
        return the underlying FastAPI instance.
        """
        # Register webhooks first (will exit if it fails)
        self.register_webhooks()

        # Register routes
        self.register_routes()

        # Ensure MCPs are initialized via the controller / startup service
        self._issue_controller.init_mcps()

        return self._app


def create_app() -> FastAPI:
    """
    Application factory used by ASGI servers (e.g., uvicorn).

    Sets up logging and initializes all dependencies.
    """
    # Setup logging first
    setup_logging(
        log_level=logging.INFO,
        log_file="logs/app.log",
        enable_console=True,
    )

    logger.info("Initializing AI Orchestrator application...")

    container = DI()
    issue_controller = container.issue_controller()
    jira_client = container.jira_client()
    webhook_config = container.webhook_config()

    app_wrapper = FastAPIApp(
        issue_controller=issue_controller,
        jira_client=jira_client,
        webhook_config=webhook_config,
    )
    return app_wrapper.start()


# ASGI entrypoint expected by uvicorn: `uvicorn ai_orchestrator.infra.app:app`
app = create_app()


