"""
Dependency injection container for the AI Orchestrator.

Uses `dependency_injector` to wire domain, application, and infra layers.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from ai_orchestrator.application.controllers import IssueController
from ai_orchestrator.domain.mcp_startup_service import McpStartupService
from ai_orchestrator.domain.orchestrator_service import OrchestratorService
from ai_orchestrator.infra.config import AppConfig, JiraConfig, WebhookConfig
from ai_orchestrator.infra.jira_client import JiraClient
from ai_orchestrator.infra.llm_repository_openhands import OpenHandsLlmRepository


class DI(containers.DeclarativeContainer):
    """
    DI container defining how components are constructed and wired together.
    """

    wiring_config = containers.WiringConfiguration(packages=["ai_orchestrator.application"])

    # Configuration (singleton)
    app_config = providers.Singleton(AppConfig)
    jira_config = providers.Singleton(JiraConfig)
    webhook_config = providers.Singleton(WebhookConfig)

    # Infra: Jira client
    jira_client = providers.Factory(
        JiraClient,
        config=jira_config,
    )

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


