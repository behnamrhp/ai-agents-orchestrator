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

### Workflow Sequence

The orchestrator manages AI agents through Jira webhooks. When tasks are moved between columns, the orchestrator automatically routes them to appropriate agents.

**Key Workflow:**
1. Human moves task to "Selected for Dev" in a project starting with "ai"
2. Orchestrator receives webhook and assigns task to appropriate development agent
3. Development agent completes task and moves it to "Approved"
4. Orchestrator triggers architecture review agent
5. Architecture agent reviews and either:
   - **Rejects** → Returns to "Selected for Dev" (loop)
   - **Accepts** → Moves to "Approve by Human"
6. Human provides final approval

See [Workflow Sequence Diagram](docs/architecture/workflow_sequence.md) for detailed sequence diagram and implementation details.

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

### 2. Install Dependencies

```bash
# Using pip
pip install -e .

# Or using uv (recommended)
uv pip install -e .
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# LLM Configuration
LLM_API_KEY=your-api-key-here
LLM_MODEL=anthropic/claude-sonnet-4-5-20250929
LLM_BASE_URL=

# Jira Configuration (for MCP Server)
JIRA_URL=http://176.53.196.35:8081
JIRA_USERNAME=admin
JIRA_API_TOKEN=your-jira-api-token

# Confluence Configuration (for MCP Server)
CONFLUENCE_URL=http://176.53.196.35:8090
CONFLUENCE_USERNAME=behnamrhp
CONFLUENCE_API_TOKEN=your-confluence-api-token

# MCP Server Configuration
MCP_ATLASSIAN_COMMAND=npx
MCP_ATLASSIAN_ARGS=-y,@sooperset/mcp-atlassian

# Team Contribution Rules
# General team guidelines and contribution standards
# This should contain the full text of your team contribution rules
TEAM_CONTRIBUTION_RULES=Your team contribution rules and guidelines here.

# Architecture Rules Configuration
# URL reference to architecture rules document
ARCHITECTURE_RULES_URL=https://your-confluence-instance.com/architecture-rules

# Architecture Rules Content
# Full architecture rules content that will be provided to agents
ARCHITECTURE_RULES=Your architecture rules and standards here.
```

**Note**: For multi-line content in `TEAM_CONTRIBUTION_RULES` or `ARCHITECTURE_RULES`, you can:
- Use a single line with escaped newlines (`\n`)
- Store content in a file and read it programmatically
- Use environment variable expansion if your shell supports it

### 4. Verify MCP Server Availability

The orchestrator uses `@sooperset/mcp-atlassian` which is automatically downloaded via `npx`. Ensure you have:
- Internet connection (for first-time download)
- Node.js installed (`node --version`)

## Quick Start

### Basic Usage

```python
from ai_orchestrator import AIOrchestrator
from ai_orchestrator.config import OrchestratorConfig

# Load configuration from environment
config = OrchestratorConfig()

# Initialize orchestrator
orchestrator = AIOrchestrator(config=config)

# Send a message to the agent
orchestrator.send_message("List all Jira issues in the project")
orchestrator.run()

# Check cost
print(f"Cost: ${orchestrator.get_cost():.4f}")
```

### Run Example

```bash
# Set environment variables
export LLM_API_KEY="your-api-key"

# Run example
python examples/basic_mcp_connection.py
```

## Project Structure

```
ai-orchestrator/
├── src/
│   └── ai_orchestrator/
│       ├── __init__.py
│       ├── config.py          # Configuration management
│       └── orchestrator.py    # Main orchestrator class
├── examples/
│   └── basic_mcp_connection.py
├── docs/
│   ├── architecture/
│   └── guidelines/
│       └── mcp_connection_guide.md
├── pyproject.toml
├── .env.example
└── README.md
```

## Configuration

### LLM Configuration

- `LLM_API_KEY`: Your LLM provider API key (required)
- `LLM_MODEL`: Model identifier (default: `anthropic/claude-sonnet-4-5-20250929`)
- `LLM_BASE_URL`: Base URL for custom LLM endpoints (optional)

### Atlassian Configuration

- `JIRA_URL`: Self-hosted Jira instance URL
- `JIRA_USERNAME`: Jira username
- `JIRA_API_TOKEN`: Jira API token (generate from Jira settings)
- `CONFLUENCE_URL`: Self-hosted Confluence instance URL
- `CONFLUENCE_USERNAME`: Confluence username
- `CONFLUENCE_API_TOKEN`: Confluence API token

### MCP Configuration

- `MCP_ATLASSIAN_COMMAND`: Command to run MCP server (default: `npx`)
- `MCP_ATLASSIAN_ARGS`: Arguments for MCP server (default: `-y,@sooperset/mcp-atlassian`)

### Team and Architecture Rules Configuration

These environment variables provide project-specific rules and guidelines that are loaded directly (not from Confluence) and provided to agents. Rules are mapped based on the project identifier extracted from Jira issue titles.

**Format**: `{RULE_TYPE}_{PROJECT_IDENTIFIER}` (uppercase, hyphens replaced with underscores)

**Example**: Issue title `[backend] Add authentication` → extracts `backend` → looks up:
- `TEAM_CONTRIBUTION_RULES_BACKEND`
- `ARCHITECTURE_RULES_URL_BACKEND`
- `ARCHITECTURE_RULES_BACKEND`

**Variables per project**:
- `TEAM_CONTRIBUTION_RULES_{PROJECT_IDENTIFIER}`: Project-specific team guidelines and contribution standards
- `ARCHITECTURE_RULES_URL_{PROJECT_IDENTIFIER}`: URL reference to project-specific architecture rules document
- `ARCHITECTURE_RULES_{PROJECT_IDENTIFIER}`: Full project-specific architecture rules content

**Note**: For multi-line content, you can use escaped newlines (`\n`) or store content in a file and read it programmatically in your orchestrator implementation.

### Project Repository Mapping

Map project identifiers (extracted from Jira issue titles) to repository URLs:

- Format: `PROJECT_REPO_{PROJECT_IDENTIFIER}` (uppercase, hyphens replaced with underscores)
- Example: Issue title `[backend] Add authentication` → extracts `backend` → looks up `PROJECT_REPO_BACKEND`
- Multiple mappings can be defined:
  - `PROJECT_REPO_BACKEND`: Repository URL for backend projects
  - `PROJECT_REPO_WEB_FRONT`: Repository URL for web frontend projects
  - `PROJECT_REPO_APP_FRONT`: Repository URL for app frontend projects
  - Add more as needed for your projects

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

1. **Check API Key**: Verify `LLM_API_KEY` is set correctly
2. **Check Model**: Ensure model identifier is correct for your provider
3. **Check Base URL**: For custom endpoints, verify `LLM_BASE_URL` is correct

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

## Roadmap

- [ ] Webhook support for triggering agents (design complete - see [Workflow Sequence](docs/architecture/workflow_sequence.md))
- [ ] Multi-agent orchestration (Development + Architecture agents)
- [ ] Agent team management
- [ ] Workflow definitions (Jira board column mapping)
- [ ] Integration with CI/CD pipelines
- [ ] Monitoring and observability
- [ ] Webhook endpoint implementation
- [ ] Agent routing logic based on project naming

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

