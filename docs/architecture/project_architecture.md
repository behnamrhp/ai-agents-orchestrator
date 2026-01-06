## Project Architecture

This document describes the high-level code architecture of the AI Orchestrator service that:

- Accepts Jira webhooks for issue changes.
- Uses an **app layer** (FastAPI) to expose HTTP routes.
- Uses a **repository/orchestration layer** to coordinate logic and connect to **OpenHands**.
- Manages **Atlassian MCP** connection to OpenHands via a dedicated startup service.

---

## Sequence Diagram – Startup & Webhook Handling

```plantuml
@startuml
skinparam sequenceMessageAlign center
skinparam participant {
    BackgroundColor #E8F4F8
    BorderColor #2E86AB
}
skinparam actor {
    BackgroundColor #F0F8FF
    BorderColor #003366
}

actor "Jira\n(Webhooks)" as Jira
participant "FastAPI Router\n(App Layer)" as Router
participant "IssueController\n(App Layer)" as IssueController
participant "OrchestratorService\n(Domain)" as OrchestratorSvc
participant "LLM Repository\n(OpenHands)" as LlmRepo
participant "MCP Startup Service\n(Domain)" as MCPService

== Service Startup ==

Router -> MCPService: onStartup()\nEnsure Atlassian MCP connected (via LLM Repo)
activate MCPService

MCPService -> LlmRepo: checkOpenHandsForAtlassianMcp()
LlmRepo --> MCPService: connectionStatus (connected?/not connected)

alt Atlassian MCP not connected in OpenHands
    MCPService -> LlmRepo: connectAtlassianMcp()
    LlmRepo --> MCPService: mcpConnected
else Atlassian MCP already connected
    MCPService -> MCPService: Skip connect\n(log "already connected")
end

deactivate MCPService

Router -> Router: registerRoutes()\n/issue-created, /issue-updated

== Webhook: Issue Created ==

Jira -> Router: POST /webhooks/jira/issue-created\n(issue payload)
activate Router

Router -> IssueController: handleIssueCreated(payload)
activate IssueController

IssueController -> OrchestratorSvc: handleIssueCreated(eventDto)
activate OrchestratorSvc

OrchestratorSvc -> OrchestratorSvc: map DTO → domain Issue
OrchestratorSvc -> LlmRepo: assignAgent(domainIssue)
activate LlmRepo
LlmRepo --> OrchestratorSvc: assignmentResult / ack
deactivate LlmRepo

OrchestratorSvc --> IssueController: createdIssue / status
deactivate OrchestratorSvc

IssueController --> Router: HTTP 200\n(acknowledge webhook)
deactivate IssueController
deactivate Router

== Webhook: Issue Updated ==

Jira -> Router: POST /webhooks/jira/issue-updated\n(issue payload)
activate Router

Router -> IssueController: handleIssueUpdated(payload)
activate IssueController

IssueController -> OrchestratorSvc: handleIssueUpdated(eventDto)
activate OrchestratorSvc

OrchestratorSvc -> OrchestratorSvc: apply domain rules\n(status/label checks, etc.)
OrchestratorSvc -> LlmRepo: assignAgent(domainIssue)
activate LlmRepo
LlmRepo --> OrchestratorSvc: updatedAssignment / status
deactivate LlmRepo

OrchestratorSvc --> IssueController: updatedIssue / status
deactivate OrchestratorSvc

IssueController --> Router: HTTP 200\n(acknowledge webhook)
deactivate IssueController
deactivate Router

@enduml
```

---

## Class Diagram – Layers & Dependencies

```plantuml
@startuml
skinparam packageStyle rectangle

package "Domain" {
  class Issue {
    +id: str
    +key: str
    +projectKey: str
    +status: str
    +labels: List[str]
    +summary: str
    +description: str
    +project_repo_url: str
    +team_contribution_rules_url: str
    +team_architecture_rules_url: str
    +prd_url:str
    +ard_url:str
  }

  class OrchestratorService {
    -llmRepository: LlmRepository
    +assignAgent(issue: Issue, prompt: str): None
  }

  class McpStartupService {
    -llmRepository: LlmRepository
    +onStartup(): None
  }

  interface LlmRepository {
    +checkMcpConnection(provider: str): bool
    +connectMcp(provider: str): None
    +assignAgent(issue: Issue, prompt: string): None
  }
}

package "Application Layer" {
  class FastAPIApp {
    +registerRoutes()
    +start()
  }

  class IssueController {
    +handleIssueCreated(issue: Issue): None
    +initMCPs(): None
  }
}

package "Infra (FastAPI, Config, DI)" {
  class DI {}
  note top
  This is the dependency injection container.
  It is used to inject the dependencies into the classes.
  Run the fask api 
  end note

  class OpenHandsLlmRepository  {
    +checkMcpConnection(provider: str): bool
    +connectMcp(provider: str): None
    +assignAgent(issue: Issue, prompt: string): None
  }
}
OpenHandsLlmRepository ..|> LlmRepository

IssueController --> McpStartupService : depends on (injected)
IssueController --> OrchestratorService : depends on (injected)
FastAPIApp --> IssueController  : depends on (injected)

OrchestratorService --> Issue : uses
OrchestratorService --> LlmRepository : depends on

LlmRepository <|.. OpenHandsLlmRepository

McpStartupService --> LlmRepository : depends on

@enduml
```

---

### Dependency Injection & Responsibilities

- **App layer**
  - Contains HTTP endpoints and controllers that translate Jira webhook payloads into `IssueEventDTO` domain objects.
  - Does **not** talk to OpenHands directly; it only depends on the domain `OrchestratorService`.
- **Domain layer**
  - Owns core domain models (`Issue`, `IssueEventDTO`), the `LlmRepository` interface, and services `OrchestratorService` and `McpStartupService`.
  - `OrchestratorService` takes domain `Issue` objects and calls `LlmRepository.assignAgent(issue)` for both created and updated hooks.
  - `McpStartupService` ensures Atlassian MCP is connected at startup via `LlmRepository.checkMcpConnection` / `connectMcp`.
- **Infra layer**
  - Hosts the FastAPI application (`FastAPIApp`), configuration, and dependency injection wiring.
  - Provides `OpenHandsLlmRepository` as the concrete `LlmRepository` implementation, encapsulating all calls to OpenHands and Atlassian MCP.
  - On startup, wires `McpStartupService` (from the domain layer) to ensure MCP is connected before serving requests.


