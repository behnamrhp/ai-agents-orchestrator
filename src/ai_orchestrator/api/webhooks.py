"""FastAPI application entrypoint and HTTP route wiring (API layer)."""

from __future__ import annotations

from fastapi import Depends, FastAPI

from ..domain import IssueEventDTO
from ..domain_services import McpStartupService, OrchestratorService
from ..infra_openhands import OpenHandsClient


def get_orchestrator_service() -> OrchestratorService:
    """Create the domain OrchestratorService with an OpenHands-based LLM repository.

    In a real application we might want to use a proper DI container,
    but for the initial skeleton this function is sufficient.
    """

    llm_repo = OpenHandsClient()
    return OrchestratorService(llm_repository=llm_repo)


def create_app() -> FastAPI:
    app = FastAPI(title="AI Orchestrator Jira Webhook API")

    # Wire startup hook to ensure MCP is connected inside OpenHands
    llm_repo = OpenHandsClient()
    startup_service = McpStartupService(llm_repository=llm_repo)

    @app.on_event("startup")
    def _startup() -> None:
        startup_service.on_startup()

    @app.post("/webhooks/jira/issue-created")
    def issue_created(
        event: IssueEventDTO,
        orchestrator: OrchestratorService = Depends(get_orchestrator_service),
    ):
        """Handle Jira issue created webhook."""
        issue = orchestrator.handle_issue_created(event)
        return {"status": "ok", "issue_key": issue.key}

    @app.post("/webhooks/jira/issue-updated")
    def issue_updated(
        event: IssueEventDTO,
        orchestrator: OrchestratorService = Depends(get_orchestrator_service),
    ):
        """Handle Jira issue updated webhook."""
        issue = orchestrator.handle_issue_updated(event)
        return {"status": "ok", "issue_key": issue.key}

    return app


app = create_app()


