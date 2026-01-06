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
participant "FastAPI App\n(App Layer)" as App
participant "IssueController\n(App Layer)" as IssueController
participant "Repository Layer\n(IssueRepository)" as Repo
participant "OpenHands Client\n(Infra)" as OH
participant "MCP Startup Service\n(Atlassian MCP)" as MCPService

== Service Startup ==

App -> MCPService: onStartup()\nEnsure Atlassian MCP connected (via OpenHands)
activate MCPService

MCPService -> OH: checkOpenHandsForAtlassianMcp()
OH --> MCPService: connectionStatus (connected?/not connected)

alt Atlassian MCP not connected in OpenHands
    MCPService -> OH: connectAtlassianMcp()
    OH --> MCPService: mcpConnected
else Atlassian MCP already connected
    MCPService -> MCPService: Skip connect\n(log "already connected")
end

deactivate MCPService

App -> App: registerRoutes()\n/issue/create, /issue/update

== Webhook: Issue Created/Updated ==

Jira -> App: POST /webhooks/jira/issue-created\n(issue payload)
activate App

App -> IssueController: handleIssueCreated(payload)
activate IssueController

IssueController -> Repo: createIssue(eventDto)\n(via IssueRepository interface)
activate Repo

Repo -> Repo: map DTO → domain model
Repo -> OH: dispatchToOpenHands(domainIssue)\n(e.g., run workflow/agent)
activate OH
OH --> Repo: result / workflow status
deactivate OH

Repo --> IssueController: createdIssue / status
deactivate Repo

IssueController --> App: HTTP 200\n(acknowledge webhook)
deactivate IssueController
deactivate App

== Webhook: Issue Updated ==

Jira -> App: POST /webhooks/jira/issue-updated\n(issue payload)
activate App

App -> IssueController: handleIssueUpdated(payload)
activate IssueController

IssueController -> Repo: updateIssue(eventDto)\n(via IssueRepository interface)
activate Repo

Repo -> Repo: apply domain rules\n(status/label checks, etc.)
Repo -> OH: updateOpenHandsWorkflow(domainIssue)
activate OH
OH --> Repo: result / updated status
deactivate OH

Repo --> IssueController: updatedIssue / status
deactivate Repo

IssueController --> App: HTTP 200\n(acknowledge webhook)
deactivate IssueController
deactivate App

@enduml
```

---

## Class Diagram – Layers & Dependencies

```plantuml
@startuml
skinparam packageStyle rectangle

package "App Layer (FastAPI)" {
  class FastAPIApp {
    +registerRoutes()
    +start()
  }

  class IssueController {
    -issueRepository: IIssueRepository
    +handleIssueCreated(request, reply)
    +handleIssueUpdated(request, reply)
  }
}

package "Domain" {
  class Issue {
    +id: str
    +key: str
    +projectKey: str
    +status: str
    +labels: List[str]
    +summary: str
    +description: str
  }

  class IssueEventDTO {
    +fromJiraPayload(payload): IssueEventDTO
  }
}

package "Repository / Orchestration Layer" {
  interface IIssueRepository {
    +createIssue(event: IssueEventDTO): Issue
    +updateIssue(event: IssueEventDTO): Issue
    +ensureMcpConnected(): None
  }

  class IssueRepositoryImpl {
    -openHandsClient: IOpenHandsClient
    +createIssue(event: IssueEventDTO): Issue
    +updateIssue(event: IssueEventDTO): Issue
    +ensureMcpConnected(): None
    -mapToDomain(event: IssueEventDTO): Issue
  }
}

package "Infrastructure" {
  interface IOpenHandsClient {
    +checkMcpConnection(provider: str): bool
    +connectMcp(provider: str): None
    +dispatchIssue(issue: Issue): None
    +updateIssue(issue: Issue): None
  }

  class OpenHandsClient implements IOpenHandsClient {
    +checkMcpConnection(provider: str): bool
    +connectMcp(provider: str): None
    +dispatchIssue(issue: Issue): None
    +updateIssue(issue: Issue): None
  }

  class McpStartupService {
    -issueRepository: IIssueRepository
    +onStartup(): None
  }
}

FastAPIApp --> IssueController : creates / injects
IssueController --> IIssueRepository : depends on (injected)
IIssueRepository <|.. IssueRepositoryImpl

IssueRepositoryImpl --> IOpenHandsClient : depends on (injected)
IOpenHandsClient <|.. OpenHandsClient

IssueRepositoryImpl --> Issue : uses
IssueRepositoryImpl --> IssueEventDTO : uses

McpStartupService --> IIssueRepository : depends on
McpStartupService ..> IOpenHandsClient : via repository.ensureMcpConnected()

@enduml
```

---

### Dependency Injection & Responsibilities

- **FastAPI app layer**
  - Owns HTTP server and route registration.
  - Injects `IIssueRepository` into `IssueController`.
- **Repository layer**
  - Implements `IIssueRepository` (`IssueRepositoryImpl`).
  - Orchestrates domain mapping and calls to `OpenHandsClient`.
  - Exposes `ensureMcpConnected()` used by `McpStartupService` to check/connect Atlassian MCP.
- **Infrastructure**
  - `OpenHandsClient` encapsulates all calls to OpenHands and MCP.
  - `McpStartupService` runs on startup, uses repository interface to ensure MCP connection before the app starts serving webhooks.


