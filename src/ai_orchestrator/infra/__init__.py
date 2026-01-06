"""
Infrastructure layer package.

Hosts framework integrations (FastAPI), configuration, and dependency
injection wiring. Concrete implementations of domain interfaces live here.
"""

"""Infrastructure layer: DI container and OpenHands-based LLM repository."""

from .container import container  # re-export for easy access


