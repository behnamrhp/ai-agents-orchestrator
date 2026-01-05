"""Example: Basic MCP connection to Jira and Confluence."""

import os
import sys
from pathlib import Path

# Add src to path for development (if not installed as package)
src_path = Path(__file__).parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from ai_orchestrator import AIOrchestrator
from ai_orchestrator.config import OrchestratorConfig


def main():
    """Example of connecting to Jira and Confluence via MCP."""
    # Load configuration from environment
    config = OrchestratorConfig()

    # Initialize orchestrator
    orchestrator = AIOrchestrator(config=config)

    # Example: Query Jira issues
    print("=" * 80)
    print("Example 1: Querying Jira issues")
    print("=" * 80)
    orchestrator.send_message(
        "Can you list the recent Jira issues from the project? "
        "Use the Jira MCP tools to fetch issues."
    )
    orchestrator.run()

    # Example: Read Confluence page
    print("\n" + "=" * 80)
    print("Example 2: Reading Confluence page")
    print("=" * 80)
    orchestrator.send_message(
        "Can you search for pages in Confluence related to 'architecture'? "
        "Use the Confluence MCP tools."
    )
    orchestrator.run()

    # Report cost
    cost = orchestrator.get_cost()
    print("\n" + "=" * 80)
    print(f"Total cost: ${cost:.4f}")
    print("=" * 80)


if __name__ == "__main__":
    main()

