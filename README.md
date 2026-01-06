# AI Orchestrator

AI Orchestrator for managing AI-driven development processes with OpenHands SDK and MCP (Model Context Protocol) integration.

## Overview

This orchestrator enables AI-driven development workflows by:
- Managing AI agents using OpenHands SDK
- Integrating with external services via MCP (Jira, Confluence, etc.)
- Providing a structured approach to human-AI collaboration
- Supporting webhook-driven agent execution (coming soon)

## Architecture

### Team Structure

```
┌─────────────────────────────────────────────┐
│                HUMAN TEAMS                  │
│        (Limited • Accountable • Decision)   │
│                                             │
│  ┌──────────────┐   ┌──────────────────┐   │
│  │ Architecture │   │ Backend Team     │   │
│  │ Team         │   │ (Humans)         │   │
│  │ (Humans)     │   └──────────────────┘   │
│  │              │   ┌──────────────────┐   │
│  │ - Design     │   │ Web Front Team   │   │
│  │ - Rules      │   │ (Humans)         │   │
│  │ - Governance │   └──────────────────┘   │
│  │ - Review     │   ┌──────────────────┐   │
│  │ - Agent Ctrl │   │ App Front Team   │   │
│  └──────────────┘   │ (Humans)         │   │
│                     └──────────────────┘   │
└─────────────────────────────────────────────┘
                    ⬇ governs / supervises ⬇
┌─────────────────────────────────────────────┐
│                  AI TEAMS                   │
│      (Unlimited • Parallel • Subordinate)   │
│                                             │
│  ⬢ Backend Agents        ⬢ Web Front Agents │
│    (many, scalable)        (many, scalable) │
│                                             │
│  ⬢ App Front Agents      ⬢ Architecture    │
│    (many, scalable)        Review Agents    │
│                             (compliance)   │
└─────────────────────────────────────────────┘
```

### Workflow & Code Architecture

- **Workflow Sequence**: The orchestrator manages AI agents through Jira webhooks. When tasks are moved between columns, the orchestrator automatically routes them to appropriate agents. See [Workflow Sequence Diagram](docs/architecture/workflow_sequence.md) for the end‑to‑end Jira/agent workflow.
- **Project Code Architecture**: The service exposes a FastAPI app layer that receives Jira webhooks, delegates to a repository/orchestration layer, and uses an OpenHands client to talk to OpenHands and Atlassian MCP. See [Project Architecture](docs/architecture/project_architecture.md) for sequence and class diagrams of the code layout.

## Features

- ✅ OpenHands SDK integration
- ✅ MCP server support (Jira, Confluence)
- ✅ Configurable agent management
- ✅ Security analyzer integration
- ✅ Cost tracking
- 🚧 Webhook support (Jira webhook integration - see workflow)
- 🚧 Multi-agent orchestration (Development + Architecture agents)

## Prerequisites

- Python 3.10+
- Node.js 18+ (for MCP servers via npx)
- LLM API key (Anthropic, OpenAI, etc.)
- Access to self-hosted Jira and Confluence instances

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-orchestrator
```

### 2. Create Virtual Environment

**Important**: On Arch Linux, Manjaro, and other systems with externally-managed Python environments, you must use a virtual environment.

```bash
# Create virtual environment
# If 'python' command points to Cursor AppImage, use system Python explicitly:
/usr/bin/python3 -m venv venv

# Or if python3 points to system Python:
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Verify activation (you should see (venv) in your prompt)
```

### 3. Install Dependencies

```bash
# Using pip (with virtual environment activated)
pip install -e .

# Or using uv (recommended, faster)
uv pip install -e .
```

**Note**: If you encounter "externally-managed-environment" error, make sure you've activated the virtual environment before running pip install.

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration. **ALL environment variables are REQUIRED**. The application will fail to start or process issues if any required environment variable is missing.

See `.env.example` for a complete template with all required options.

#### Core Configuration (Required)

```env
# LLM Configuration
LLM_MODEL=deepseek
# LLM_API_KEY (Optional) - If not provided, LLM credentials may be configured in OpenHands
LLM_API_KEY=
# LLM_BASE_URL (Optional) - If not provided, uses provider's default endpoint
LLM_BASE_URL=

# Jira Configuration (Required)
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token

# Webhook Configuration (Required)
WEBHOOK_BASE_URL=http://localhost:8000
WEBHOOK_ENABLED=true

# Confluence Configuration (Required)
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your-confluence-api-token

# MCP Server Configuration (Required)
MCP_ATLASSIAN_COMMAND=npx
MCP_ATLASSIAN_ARGS=-y,@sooperset/mcp-atlassian
```

#### Project-Specific Configuration (Required)

These variables are dynamically mapped based on the project identifier extracted from Jira issue titles. The project identifier is extracted from issue summaries using the pattern `[identifier]` (e.g., `[backend] Add feature` → extracts `backend`).

**Format**: `{VAR_NAME}_{PROJECT_IDENTIFIER}` (uppercase, hyphens replaced with underscores)

**Example**: Issue title `[backend] Add authentication` extracts `backend` → normalizes to `BACKEND` → looks up:
- `PROJECT_REPO_BACKEND` **(Required)**
- `TEAM_CONTRIBUTION_RULES_URL_BACKEND` **(Required)**
- `ARCHITECTURE_RULES_URL_BACKEND` **(Required)**
- `PRD_URL_BACKEND` **(Required)**
- `ARD_URL_BACKEND` **(Required)**

**ALL project-specific variables are REQUIRED for each project identifier.** If any are missing, the application will fail with an error log.

```env
# Project Repository URLs (Required)
# Maps to: PROJECT_REPO_{PROJECT_IDENTIFIER}
PROJECT_REPO_BACKEND=https://github.com/your-org/backend-repo
PROJECT_REPO_WEB_FRONT=https://github.com/your-org/web-frontend-repo
# Add more as needed: PROJECT_REPO_{YOUR_PROJECT_IDENTIFIER}

# Team Contribution Rules URLs (Required)
# Maps to: TEAM_CONTRIBUTION_RULES_URL_{PROJECT_IDENTIFIER}
TEAM_CONTRIBUTION_RULES_URL_BACKEND=https://your-confluence-instance.com/team-contribution-rules
TEAM_CONTRIBUTION_RULES_URL_WEB_FRONT=https://your-confluence-instance.com/team-contribution-rules
# Add more as needed: TEAM_CONTRIBUTION_RULES_URL_{YOUR_PROJECT_IDENTIFIER}

# Architecture Rules URLs (Required)
# Maps to: ARCHITECTURE_RULES_URL_{PROJECT_IDENTIFIER}
ARCHITECTURE_RULES_URL_BACKEND=https://your-confluence-instance.com/architecture-rules
ARCHITECTURE_RULES_URL_WEB_FRONT=https://your-confluence-instance.com/architecture-rules
# Add more as needed: ARCHITECTURE_RULES_URL_{YOUR_PROJECT_IDENTIFIER}

# Product Requirements Document URLs (Required)
# Maps to: PRD_URL_{PROJECT_IDENTIFIER}
PRD_URL_BACKEND=https://your-confluence-instance.com/prd/backend
PRD_URL_WEB_FRONT=https://your-confluence-instance.com/prd/web-frontend
# Add more as needed: PRD_URL_{YOUR_PROJECT_IDENTIFIER}

# Architecture Requirements Document URLs (Required)
# Maps to: ARD_URL_{PROJECT_IDENTIFIER}
ARD_URL_BACKEND=https://your-confluence-instance.com/ard/backend
ARD_URL_WEB_FRONT=https://your-confluence-instance.com/ard/web-frontend
# Add more as needed: ARD_URL_{YOUR_PROJECT_IDENTIFIER}
```

**Important Notes**:
- **All environment variables are REQUIRED**. Missing variables will cause the application to fail with error logs.
- Project identifiers are automatically extracted from Jira issue titles. If an issue title starts with `[identifier]`, that identifier is used. Otherwise, the system checks issue labels for matching environment variables.
- You must define all 5 project-specific variables (`PROJECT_REPO_*`, `TEAM_CONTRIBUTION_RULES_URL_*`, `ARCHITECTURE_RULES_URL_*`, `PRD_URL_*`, `ARD_URL_*`) for each project identifier you plan to use.

### 5. Verify MCP Server Availability

The orchestrator uses `@sooperset/mcp-atlassian` which is automatically downloaded via `npx`. Ensure you have:
- Internet connection (for first-time download)
- Node.js installed (`node --version`)

## Quick Start

### Run the FastAPI Webhook Server

Start the FastAPI application that will receive Jira webhooks:

```bash
uvicorn ai_orchestrator.infra.app:app --reload
```

By default this will listen on `http://127.0.0.1:8000`. The application will automatically:

1. **Set up logging** with timestamps and stacktraces
2. **Test Jira connection** using your `JIRA_URL`, `JIRA_USERNAME`, and `JIRA_API_TOKEN`
3. **Register webhooks with Jira** (if `WEBHOOK_ENABLED=true`)
   - Registers webhooks for `issue_created` and `issue_updated` events
   - Uses `WEBHOOK_BASE_URL` as the callback URL
4. **Initialize MCP connections** for Atlassian services
5. **Start serving webhook endpoints**:
   - `POST /webhooks/jira/issue-created`
   - `POST /webhooks/jira/issue-updated`

**Important**: 
- If Jira connection fails, the application will exit with an error. Check your Jira configuration.
- If webhook registration fails, the application will exit with an error. Ensure `WEBHOOK_BASE_URL` is publicly accessible and `WEBHOOK_ENABLED=true`.
- For local development, use a tool like [ngrok](https://ngrok.com/) to expose your local server: `ngrok http 8000` and set `WEBHOOK_BASE_URL` to the ngrok URL.

### Classic Orchestrator Usage (optional)

You can still use the lower‑level `AIOrchestrator` directly for experiments:

```python
from ai_orchestrator import AIOrchestrator
from ai_orchestrator.config import OrchestratorConfig

config = OrchestratorConfig()
orchestrator = AIOrchestrator(config=config)
orchestrator.send_message("List all Jira issues in the project")
orchestrator.run()
print(f"Cost: ${orchestrator.get_cost():.4f}")
```

## Project Structure

```
ai-orchestrator/
├── src/
│   └── ai_orchestrator/
│       ├── __init__.py
│       ├── config.py             # Configuration management
│       ├── orchestrator.py       # Low‑level AIOrchestrator (OpenHands SDK wrapper)
│       ├── app.py                # FastAPI app + routes for Jira webhooks
│       ├── domain.py             # Domain models (Issue, IssueEventDTO)
│       ├── interfaces.py         # IIssueRepository, IOpenHandsClient
│       ├── repository.py         # IssueRepositoryImpl orchestration layer
│       ├── infra_openhands.py    # OpenHandsClient (IOpenHandsClient implementation)
│       └── services.py           # McpStartupService and other services
├── examples/
│   └── basic_mcp_connection.py
├── docs/
│   ├── architecture/
│   │   ├── workflow_sequence.md
│   │   └── project_architecture.md
│   └── guidelines/
│       └── mcp_connection_guide.md
├── pyproject.toml
├── .env.example
└── README.md
```

## Configuration

### Environment Variables

**ALL environment variables are REQUIRED.** The application will fail to start or process issues if any required environment variable is missing.

#### Core Configuration (Required)

- `LLM_MODEL` **(Required)**: Model identifier used by OpenHands (e.g., `deepseek`, `anthropic/claude-3-5-sonnet`)
- `LLM_API_KEY` **(Optional)**: API key for the underlying LLM provider (OpenAI, Anthropic, DeepSeek, etc.)
  - Optional: If not provided, LLM credentials may be configured in OpenHands itself
- `LLM_BASE_URL` **(Optional)**: Base URL for LLM endpoints
  - Optional: If not provided, uses the provider's default endpoint

- `JIRA_URL` **(Required)**: Jira instance base URL (e.g., `https://your-domain.atlassian.net`)
- `JIRA_USERNAME` **(Required)**: Jira username/email for API authentication
- `JIRA_API_TOKEN` **(Required)**: Jira API token (generate from Jira account settings → Security → API tokens)

- `WEBHOOK_BASE_URL` **(Required)**: Publicly accessible URL where Jira can send webhooks
  - Production: `https://your-app.example.com`
  - Development: `https://your-ngrok-url.ngrok.io`
  - Local testing: `http://localhost:8000` (only works if Jira can reach it)
- `WEBHOOK_ENABLED` **(Required)**: Set to `true` to register webhooks on startup, `false` to skip registration

- `CONFLUENCE_URL` **(Required)**: Confluence instance base URL
- `CONFLUENCE_USERNAME` **(Required)**: Confluence username for API authentication
- `CONFLUENCE_API_TOKEN` **(Required)**: Confluence API token

- `MCP_ATLASSIAN_COMMAND` **(Required)**: Command to run MCP server (e.g., `npx`)
- `MCP_ATLASSIAN_ARGS` **(Required)**: Arguments for MCP server (e.g., `-y,@sooperset/mcp-atlassian`)

#### OpenHands Self-Hosted Configuration (Required if using remote OpenHands)
- `OPENHANDS_RUNTIME_API_URL` **(Required if using remote OpenHands)**: URL of self-hosted OpenHands instance (e.g., `http://your-server:3000` or `https://openhands.yourdomain.com`)
  - If set, the app will connect to the remote OpenHands instance
  - If not set, uses local Conversation (default)
- `OPENHANDS_RUNTIME_API_KEY` **(Required if your OpenHands server requires authentication)**: API key for self-hosted OpenHands instance
  - Get this from your OpenHands admin dashboard → Settings → API Keys
  - Leave empty if your server doesn't require authentication
- `OPENHANDS_SERVER_IMAGE` (Optional, default: `ghcr.io/openhands/agent-server:latest-python`): Docker image for the agent server

### Project-Specific Environment Variables

These variables are dynamically mapped based on the project identifier extracted from Jira issue titles. The project identifier is extracted from issue summaries using the pattern `[identifier]` (e.g., `[backend] Add feature` → extracts `backend`).

**Format**: `{VAR_NAME}_{PROJECT_IDENTIFIER}` (uppercase, hyphens replaced with underscores)

**Example**: Issue title `[backend] Add authentication` extracts `backend` → normalizes to `BACKEND` → looks up:
- `PROJECT_REPO_BACKEND`
- `TEAM_CONTRIBUTION_RULES_URL_BACKEND`
- `ARCHITECTURE_RULES_URL_BACKEND`
- `PRD_URL_BACKEND` (optional)
- `ARD_URL_BACKEND` (optional)

#### Project Repository URLs
- Format: `PROJECT_REPO_{PROJECT_IDENTIFIER}`
- Example: `PROJECT_REPO_BACKEND=https://github.com/your-org/backend-repo`
- Multiple mappings can be defined:
  - `PROJECT_REPO_BACKEND`: Repository URL for backend projects
  - `PROJECT_REPO_WEB_FRONT`: Repository URL for web frontend projects
  - `PROJECT_REPO_APP_FRONT`: Repository URL for app frontend projects
  - Add more as needed: `PROJECT_REPO_{YOUR_PROJECT_IDENTIFIER}`

#### Team Contribution Rules URLs
- Format: `TEAM_CONTRIBUTION_RULES_URL_{PROJECT_IDENTIFIER}`
- Example: `TEAM_CONTRIBUTION_RULES_URL_BACKEND=https://confluence.example.com/team-contribution-rules`
- Provides URL reference to project-specific team contribution guidelines and standards

#### Architecture Rules URLs
- Format: `ARCHITECTURE_RULES_URL_{PROJECT_IDENTIFIER}`
- Example: `ARCHITECTURE_RULES_URL_BACKEND=https://confluence.example.com/architecture-rules`
- Provides URL reference to project-specific architecture rules document

#### Product Requirements Document URLs (Required)
- Format: `PRD_URL_{PROJECT_IDENTIFIER}`
- Example: `PRD_URL_BACKEND=https://confluence.example.com/prd/backend`
- Provides URL reference to Product Requirements Document

#### Architecture Requirements Document URLs (Required)
- Format: `ARD_URL_{PROJECT_IDENTIFIER}`
- Example: `ARD_URL_BACKEND=https://confluence.example.com/ard/backend`
- Provides URL reference to Architecture Requirements Document

**Important**: 
- **ALL project-specific variables are REQUIRED** for each project identifier you plan to use.
- If any project-specific environment variable is missing when processing an issue, the application will fail with an error log.
- Project identifiers are automatically extracted from Jira issue titles. If an issue title starts with `[identifier]`, that identifier is used. Otherwise, the system checks issue labels for matching environment variables.
- You must define all 5 project-specific variables (`PROJECT_REPO_*`, `TEAM_CONTRIBUTION_RULES_URL_*`, `ARCHITECTURE_RULES_URL_*`, `PRD_URL_*`, `ARD_URL_*`) for each project identifier.

The project identifier is extracted from the Jira issue title using the pattern `[project]`. The repository URL is then included in the agent context for code implementation.

## Usage Examples

### Example 1: Query Jira Issues

```python
from ai_orchestrator import AIOrchestrator
from ai_orchestrator.config import OrchestratorConfig

config = OrchestratorConfig()
orchestrator = AIOrchestrator(config=config)

orchestrator.send_message(
    "Can you list the recent Jira issues from the project? "
    "Use the Jira MCP tools to fetch issues."
)
orchestrator.run()
```

### Example 2: Read Confluence Pages

```python
orchestrator.send_message(
    "Can you search for pages in Confluence related to 'architecture'? "
    "Use the Confluence MCP tools."
)
orchestrator.run()
```

### Example 3: Custom Workspace

```python
orchestrator = AIOrchestrator(
    config=config,
    workspace="/path/to/workspace",
)
```

### Example 4: Tool Filtering

```python
# Only allow specific MCP tools
orchestrator = AIOrchestrator(
    config=config,
    filter_tools_regex="^atlassian.*jira.*$",  # Only Jira tools
)
```

## MCP Integration

The orchestrator integrates with MCP servers to provide dynamic tool access. See [MCP Connection Guide](docs/guidelines/mcp_connection_guide.md) for detailed information.

### Supported MCP Servers

- **Atlassian**: Jira and Confluence integration via `@sooperset/mcp-atlassian`
- **Extensible**: Add more MCP servers by updating the configuration

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Or with uv
uv pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ examples/
ruff check src/ examples/
```

## Troubleshooting

### MCP Server Not Connecting

1. **Check Node.js**: Ensure Node.js is installed (`node --version`)
2. **Check Network**: Ensure internet access for `npx` to download packages
3. **Check Environment Variables**: Verify all required env vars are set
4. **Check Logs**: Review orchestrator logs for MCP connection errors

### Authentication Issues

1. **Verify API Tokens**: Ensure Jira/Confluence API tokens are valid
2. **Check Permissions**: Verify tokens have required permissions
3. **Test URLs**: Verify Jira/Confluence URLs are accessible

### LLM Issues

1. **Check API Key**: If using `LLM_API_KEY`, verify it's set correctly. If not set, ensure LLM credentials are configured in OpenHands
2. **Check Model**: Ensure model identifier is correct for your provider
3. **Check Base URL**: If using `LLM_BASE_URL`, verify it's correct. If not set, the provider's default endpoint will be used

## Security

- **Never commit `.env` files**: They contain sensitive credentials
- **Use API tokens**: Generate tokens with minimal required permissions
- **Rotate tokens**: Regularly rotate API tokens
- **Network security**: Ensure secure communication with self-hosted instances

## Documentation

- **[README.md](README.md)** - This file, main runbook and setup guide
- **[Workflow Sequence Diagram](docs/architecture/workflow_sequence.md)** - Detailed workflow with Orchestrator, Jira webhooks, and agent interactions
- **[MCP Connection Guide](docs/guidelines/mcp_connection_guide.md)** - How to connect MCP servers to OpenHands
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide for immediate setup

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Add your license here]

## References

- [OpenHands SDK Documentation](https://docs.openhands.dev)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Atlassian MCP Server](https://github.com/sooperset/mcp-atlassian)

## Support

For issues and questions:
- Check [MCP Connection Guide](docs/guidelines/mcp_connection_guide.md)
- Review OpenHands SDK documentation
- Open an issue in the repository

