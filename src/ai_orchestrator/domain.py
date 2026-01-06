"""Domain models for Jira issue events and internal Issue representation."""

from typing import List, Optional

from pydantic import BaseModel


class IssueEventDTO(BaseModel):
    """Incoming Jira webhook payload (simplified DTO).

    This is intentionally generic and can be adapted as we refine
    the exact Jira webhook schema.
    """

    issue_key: str
    project_key: str
    status: str
    labels: List[str] = []
    summary: Optional[str] = None
    description: Optional[str] = None


class Issue(BaseModel):
    """Domain model representing an issue inside the orchestrator."""

    id: str
    key: str
    project_key: str
    status: str
    labels: List[str] = []
    summary: Optional[str] = None
    description: Optional[str] = None



