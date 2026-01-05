# Quick Start Guide

This guide will help you get the AI Orchestrator running with MCP integration in minutes.

## Step 1: Install Dependencies

```bash
# Install Python package
pip install -e .

# Or with uv (faster)
uv pip install -e .
```

## Step 2: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
cat > .env << EOF
# LLM Configuration
LLM_API_KEY=your-api-key-here
LLM_MODEL=deepseek

# Jira Configuration
JIRA_URL=
JIRA_USERNAME=
JIRA_API_TOKEN=

# Confluence Configuration
CONFLUENCE_URL=
CONFLUENCE_USERNAME=
CONFLUENCE_API_TOKEN=

# MCP Configuration
MCP_ATLASSIAN_COMMAND=npx
MCP_ATLASSIAN_ARGS=-y,@sooperset/mcp-atlassian
EOF
```

**Important**: Replace `your-api-key-here` with your actual LLM API key.

## Step 3: Verify Node.js

The MCP server requires Node.js. Check if it's installed:

```bash
node --version  # Should be 18+
npm --version
```

If not installed, install Node.js from [nodejs.org](https://nodejs.org/).

## Step 4: Run Example

```bash
python examples/basic_mcp_connection.py
```

## Step 5: Use in Your Code

```python
from ai_orchestrator import AIOrchestrator
from ai_orchestrator.config import OrchestratorConfig

# Load config from .env
config = OrchestratorConfig()

# Create orchestrator
orchestrator = AIOrchestrator(config=config)

# Use it
orchestrator.send_message("List Jira issues")
orchestrator.run()
```

## Troubleshooting

### "Command not found: npx"
- Install Node.js: `curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs`

### "LLM_API_KEY environment variable is not set"
- Check your `.env` file exists and contains `LLM_API_KEY`
- Ensure you're running from the project root directory

### "Connection refused" or "Cannot connect to Jira/Confluence"
- Verify the URLs are correct and accessible
- Check API tokens are valid
- Ensure network connectivity to self-hosted instances

### MCP Server Not Starting
- Check Node.js is installed: `node --version`
- Try running manually: `npx -y @sooperset/mcp-atlassian`
- Check internet connection (needed for first-time npx download)

## Next Steps

- Read the [README.md](README.md) for detailed documentation
- Check [MCP Connection Guide](docs/guidelines/mcp_connection_guide.md) for advanced configuration
- Explore the examples directory for more use cases

