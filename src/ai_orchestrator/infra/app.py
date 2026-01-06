"""
FastAPI application setup for the AI Orchestrator.

Defines the `FastAPIApp` wrapper, registers routes, and provides a
factory for the ASGI app instance.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI
from fastapi import status

from ai_orchestrator.application.controllers import IssueController
from ai_orchestrator.infra.di import DI


class FastAPIApp:
    """
    Wrapper around FastAPI to align with the architecture diagram.
    """

    def __init__(self, issue_controller: IssueController) -> None:
        self._issue_controller = issue_controller
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

    def start(self) -> FastAPI:
        """
        Initialize the application (routes and MCP startup) and
        return the underlying FastAPI instance.
        """
        self.register_routes()
        # Ensure MCPs are initialized via the controller / startup service
        self._issue_controller.init_mcps()
        return self._app


def create_app() -> FastAPI:
    """
    Application factory used by ASGI servers (e.g., uvicorn).
    """
    container = DI()
    issue_controller = container.issue_controller()
    app_wrapper = FastAPIApp(issue_controller=issue_controller)
    return app_wrapper.start()


# ASGI entrypoint expected by uvicorn: `uvicorn ai_orchestrator.infra.app:app`
app = create_app()


