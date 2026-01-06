"""
Dependency injection container for the AI Orchestrator.

Uses `dependency_injector` to wire domain, application, and infra layers.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from ai_orchestrator.domain.orchestrator_service import OrchestratorService
from ai_orchestrator.domain.mcp_startup_service import McpStartupService
from ai_orchestrator.infra.llm_repository_openhands import OpenHandsLlmRepository
from ai_orchestrator.application.controllers import IssueController


class DI(containers.DeclarativeContainer):
    """
    DI container defining how components are constructed and wired together.
    """

    wiring_config = containers.WiringConfiguration(packages=["ai_orchestrator.application"])

    # Infra: LLM repository implementation
    llm_repository = providers.Factory(
        OpenHandsLlmRepository,
        client=None,  # Placeholder; real client configuration will be added later.
    )

    # Domain services
    orchestrator_service = providers.Factory(
        OrchestratorService,
        llm_repository=llm_repository,
    )

    mcp_startup_service = providers.Factory(
        McpStartupService,
        llm_repository=llm_repository,
    )

    # Application controllers
    issue_controller = providers.Factory(
        IssueController,
        orchestrator_service=orchestrator_service,
        mcp_startup_service=mcp_startup_service,
    )


