"""
Jira client for webhook registration and API interactions.

Handles authentication and webhook registration via Jira REST API v3.
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from ai_orchestrator.infra.config import JiraConfig


class JiraClient:
    """
    Client for interacting with Jira REST API.

    Handles webhook registration and authentication.
    """

    def __init__(self, config: JiraConfig) -> None:
        """
        Initialize Jira client with configuration.

        Args:
            config: Jira configuration containing URL, username, and API token
        """
        self.config = config
        self.base_url = config.url.rstrip("/")
        self.auth = HTTPBasicAuth(config.username, config.api_token)
        self.logger = logging.getLogger(__name__)
        self._session = requests.Session()
        self._session.auth = self.auth
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def register_webhook(
        self,
        webhook_url: str,
        events: list[str] | None = None,
        jql_filter: str | None = None,
        name: str = "AI Orchestrator Webhook",
    ) -> dict[str, Any]:
        """
        Register a webhook in Jira.

        Uses Jira REST API v3: POST /rest/api/3/webhook

        Args:
            webhook_url: URL where Jira will send webhook events
            events: List of Jira events to subscribe to. Defaults to issue_created and issue_updated.
            jql_filter: Optional JQL filter to limit which issues trigger the webhook
            name: Name for the webhook in Jira

        Returns:
            Response data from Jira API

        Raises:
            requests.RequestException: If webhook registration fails
        """
        if events is None:
            events = ["jira:issue_created", "jira:issue_updated"]

        # Jira REST API v3 webhook payload format
        payload: dict[str, Any] = {
            "name": name,
            "url": webhook_url,
            "events": events,
            "excludeBody": False,
        }

        if jql_filter:
            payload["jqlFilter"] = jql_filter

        url = f"{self.base_url}/rest/api/3/webhook"

        self.logger.info(
            f"Registering webhook '{name}' at {webhook_url} for events: {', '.join(events)}"
        )

        try:
            response = self._session.post(url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            webhook_id = result.get("self", "unknown")
            self.logger.info(f"Webhook registered successfully. ID: {webhook_id}")

            return result

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error registering webhook: {e.response.status_code}"
            if e.response.text:
                error_msg += f" - {e.response.text}"
            self.logger.error(error_msg, exc_info=True)
            raise

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to register webhook: {e}", exc_info=True)
            raise

    def test_connection(self) -> bool:
        """
        Test connection to Jira API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.base_url}/rest/api/3/myself"
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            user_info = response.json()
            self.logger.info(f"Successfully connected to Jira as: {user_info.get('displayName', 'unknown')}")
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to connect to Jira: {e}", exc_info=True)
            return False

