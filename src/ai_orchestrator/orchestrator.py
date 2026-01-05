"""Main orchestrator class for managing AI agents with OpenHands."""

import os
from typing import List, Optional

from openhands.sdk import Agent, Conversation, Event, LLM, LLMConvertibleEvent, get_logger
from openhands.sdk.security.llm_analyzer import LLMSecurityAnalyzer
from openhands.sdk.tool import Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.terminal import TerminalTool

from .config import OrchestratorConfig

logger = get_logger(__name__)


class AIOrchestrator:
    """Orchestrator for managing AI agents with MCP integration."""

    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        workspace: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        filter_tools_regex: Optional[str] = None,
    ):
        """Initialize the AI Orchestrator.

        Args:
            config: Orchestrator configuration. If None, loads from environment.
            workspace: Workspace directory path. Defaults to current directory.
            tools: List of additional tools to provide to agents.
            filter_tools_regex: Regex pattern to filter MCP tools.
        """
        self.config = config or OrchestratorConfig()
        self.workspace = workspace or os.getcwd()

        # Default tools
        default_tools = [
            Tool(name=TerminalTool.name),
            Tool(name=FileEditorTool.name),
        ]

        # Combine with provided tools
        self.tools = (tools or []) + default_tools

        # Initialize LLM
        self.llm = LLM(
            usage_id="orchestrator",
            model=self.config.llm.model,
            base_url=self.config.llm.base_url,
            api_key=self.config.llm.api_key,
        )

        # Get MCP configuration
        mcp_config = self.config.get_mcp_config()

        # Initialize agent with MCP integration
        self.agent = Agent(
            llm=self.llm,
            tools=self.tools,
            mcp_config=mcp_config,
            filter_tools_regex=filter_tools_regex,
        )

        # Initialize conversation
        self.conversation = Conversation(
            agent=self.agent,
            workspace=self.workspace,
        )
        self.conversation.set_security_analyzer(LLMSecurityAnalyzer())

        logger.info("AI Orchestrator initialized with MCP integration")

    def send_message(self, message: str) -> None:
        """Send a message to the agent.

        Args:
            message: The message to send to the agent.
        """
        logger.info(f"Sending message to agent: {message[:100]}...")
        self.conversation.send_message(message)

    def run(self) -> None:
        """Run the conversation."""
        logger.info("Running conversation...")
        self.conversation.run()

    def get_cost(self) -> float:
        """Get accumulated cost from LLM usage.

        Returns:
            Accumulated cost in dollars.
        """
        return self.llm.metrics.accumulated_cost

    def get_llm_messages(self) -> List:
        """Get all LLM messages from the conversation.

        Returns:
            List of LLM messages.
        """
        messages = []

        def conversation_callback(event: Event):
            if isinstance(event, LLMConvertibleEvent):
                messages.append(event.to_llm_message())

        # Note: This requires adding the callback before running
        # For now, return empty list - can be enhanced with proper event tracking
        return messages

