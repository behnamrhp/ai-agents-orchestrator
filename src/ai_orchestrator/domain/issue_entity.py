"""
Domain models for the AI Orchestrator.

These are simple data containers for now; behavior and validation
will be introduced later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class IssueEntity:
    """Domain representation of a Jira issue."""

    id: str
    key: str
    project_key: str
    status: str
    labels: List[str]
    summary: str
    description: str

    # Additional contextual URLs for the agent (all required)
    project_repo_url: str
    team_contribution_rules_url: str
    team_architecture_rules_url: str
    prd_url: str
    ard_url: str
    
    # Optional fields must come after required fields
    team_name: Optional[str] = None


@dataclass
class IssueEventDTO:
    """
    Lightweight DTO used by the app layer to pass issue events
    into the domain layer. Mapping from the raw webhook payload
    into this DTO will be handled in the application layer.
    """

    issue: IssueEntity
    event_type: str


