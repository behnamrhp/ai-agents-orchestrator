# MCP Server Connection Guide

This guide explains how to connect the AI Orchestrator to MCP (Model Context Protocol) servers, specifically for Atlassian Jira and Confluence integration.

## Overview

The AI Orchestrator uses OpenHands SDK's MCP integration to connect to external services. MCP servers act as bridges between the AI agent and external APIs, providing tools that agents can use dynamically.

## Architecture

```
┌─────────────────┐
│  AI Orchestrator│
│  (OpenHands SDK)│
└────────┬────────┘
         │ MCP Protocol (stdio)
         │
┌────────▼────────┐
│  MCP Server     │
│  (Atlassian)    │
└────────┬────────┘
         │ REST API
         │
┌────────▼────────┐
│  Jira/Confluence│
│  (Self-hosted)  │
└─────────────────┘
```

## Prerequisites

1. **MCP Server**: The Atlassian MCP server must be available. We use `@sooperset/mcp-atlassian` which can be run via `npx` or installed locally.

2. **Atlassian Credentials**: You need:
   - Jira URL, username, and API token
   - Confluence URL, username, and API token

3. **OpenHands SDK**: The orchestrator uses OpenHands SDK which handles MCP communication.

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

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
```

### MCP Configuration Format

The orchestrator converts environment variables into OpenHands MCP configuration format:

```python
mcp_config = {
    "mcpServers": {
        "atlassian": {
            "command": "npx",  # or "node", "uvx", etc.
            "args": ["-y", "@sooperset/mcp-atlassian"],
            "env": {
                "JIRA_URL": "...",
                "JIRA_USERNAME": "...",
                "JIRA_API_TOKEN": "...",
                "CONFLUENCE_URL": "...",
                "CONFLUENCE_USERNAME": "...",
                "CONFLUENCE_API_TOKEN": "...",
            }
        }
    }
}
```

## Code Implementation

### Using the Orchestrator

```python
from ai_orchestrator import AIOrchestrator
from ai_orchestrator.config import OrchestratorConfig

# Load configuration from environment
config = OrchestratorConfig()

# Initialize orchestrator (automatically connects to MCP servers)
orchestrator = AIOrchestrator(config=config)

# Use the orchestrator
orchestrator.send_message("List all Jira issues in the project")
orchestrator.run()
```

### Manual MCP Configuration

If you need to configure MCP servers manually:

```python
from openhands.sdk import Agent, LLM
from pydantic import SecretStr

# Create MCP configuration
mcp_config = {
    "mcpServers": {
        "atlassian": {
            "command": "npx",
            "args": ["-y", "@sooperset/mcp-atlassian"],
            "env": {
                "JIRA_URL": "http://176.53.196.35:8081",
                "JIRA_USERNAME": "admin",
                "JIRA_API_TOKEN": "your-token",
                "CONFLUENCE_URL": "http://176.53.196.35:8090",
                "CONFLUENCE_USERNAME": "behnamrhp",
                "CONFLUENCE_API_TOKEN": "your-token",
            }
        }
    }
}

# Initialize LLM
llm = LLM(
    usage_id="agent",
    model="anthropic/claude-sonnet-4-5-20250929",
    api_key=SecretStr(os.getenv("LLM_API_KEY")),
)

# Create agent with MCP configuration
agent = Agent(
    llm=llm,
    tools=[],
    mcp_config=mcp_config,
)
```

## MCP Server Types

### 1. Command-based MCP Servers (stdio)

These servers run as subprocesses and communicate via stdio:

```python
mcp_config = {
    "mcpServers": {
        "server_name": {
            "command": "npx",  # or "node", "python", "uvx", etc.
            "args": ["-y", "package-name"],
            "env": {
                # Environment variables for the MCP server
            }
        }
    }
}
```

### 2. URL-based MCP Servers (HTTP)

For servers accessible via HTTP:

```python
mcp_config = {
    "mcpServers": {
        "server_name": {
            "url": "https://mcp.example.com/mcp",
            "auth": "oauth"  # or other auth types
        }
    }
}
```

## Tool Filtering

You can filter which MCP tools are available to agents using regex:

```python
orchestrator = AIOrchestrator(
    config=config,
    filter_tools_regex="^(?!repomix)(.*)|^repomix.*pack_codebase.*$",
)
```

This example allows all tools except `repomix` tools, but includes `repomix.pack_codebase`.

## Troubleshooting

### MCP Server Not Starting

1. **Check command availability**: Ensure `npx`, `node`, or the specified command is in PATH
2. **Check package exists**: Verify the MCP server package is available (e.g., `@sooperset/mcp-atlassian`)
3. **Check environment variables**: Ensure all required env vars are set correctly

### Connection Issues

1. **Verify Atlassian URLs**: Test Jira/Confluence URLs in browser
2. **Check API tokens**: Ensure tokens are valid and have proper permissions
3. **Network connectivity**: Ensure the orchestrator can reach Atlassian instances

### Tool Discovery Issues

1. **Check MCP server logs**: MCP servers may output errors to stderr
2. **Verify tool names**: Use `filter_tools_regex` to debug which tools are available
3. **Check OpenHands logs**: The SDK logs MCP tool discovery

## Local MCP Server Development

If you're developing or running a local MCP server:

```python
mcp_config = {
    "mcpServers": {
        "atlassian": {
            "command": "node",
            "args": ["/path/to/local/mcp-server/dist/index.js"],
            "env": {
                # Your environment variables
            }
        }
    }
}
```

## Security Considerations

1. **API Tokens**: Never commit API tokens to version control. Use `.env` files and `.gitignore`
2. **Environment Variables**: The orchestrator uses `pydantic-settings` to securely handle secrets
3. **Network Security**: Ensure MCP server communication happens over secure channels
4. **Token Permissions**: Use least-privilege tokens with minimal required permissions

## References

- [OpenHands MCP Documentation](https://docs.openhands.dev/sdk/guides/mcp)
- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [Atlassian MCP Server](https://github.com/sooperset/mcp-atlassian)

