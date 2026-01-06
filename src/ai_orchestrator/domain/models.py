"""
Domain models re-exports for convenience.

This module re-exports domain models from their implementation modules
to provide a consistent import path.
"""

from __future__ import annotations

from .issue_entity import IssueEntity, IssueEventDTO

__all__ = ["IssueEntity", "IssueEventDTO"]

