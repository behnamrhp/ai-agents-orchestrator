"""
Jira client for webhook registration and API interactions.

Handles authentication and webhook registration via Jira REST API.
Supports both:
- Jira Cloud: REST API v3 (/rest/api/3/) with Basic Auth (username + API token)
- Jira Server/Data Center: REST API v2 (/rest/api/2/) with either:
  - Basic Auth (username + password)
  - Bearer Token (Personal Access Token / PAT)
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
    Automatically detects Jira Cloud vs Server and uses appropriate API version.

    Authentication methods:
    - Jira Cloud: Basic Auth with username + API token
    - Jira Server/Data Center:
      - If JIRA_USERNAME is provided: Basic Auth (username + password/token)
      - If JIRA_USERNAME is empty/not set: Bearer token authentication (PAT)
    """

    def __init__(self, config: JiraConfig) -> None:
        """
        Initialize Jira client with configuration.

        Args:
            config: Jira configuration containing URL, username, and API token/PAT
        """
        self.config = config
        self.base_url = config.url.rstrip("/")
        self.logger = logging.getLogger(__name__)
        self._session = requests.Session()

        # Detect if this is Jira Cloud or Server first
        self._is_cloud = self._is_jira_cloud()

        # Configure authentication based on Jira type and credentials
        self._configure_authentication()

        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        # Detect API version based on Jira type or use configured version
        self._api_version = self._detect_api_version()

    def _is_jira_cloud(self) -> bool:
        """Check if this is a Jira Cloud instance."""
        return "atlassian.net" in self.base_url.lower()

    def _configure_authentication(self) -> None:
        """
        Configure authentication based on Jira type, config settings, and available credentials.

        Priority:
        1. Explicit auth_type from config ('basic' or 'bearer')
        2. Jira Cloud: Always Basic Auth
        3. Jira Server: Auto-detect based on username presence

        Jira Cloud: Always uses Basic Auth (email + API token)
        Jira Server/Data Center:
          - auth_type='bearer': Use Bearer token (PAT)
          - auth_type='basic': Use Basic Auth (username + password/token)
          - No auth_type + username provided: Basic Auth
          - No auth_type + no username: Bearer token (PAT)
        """
        # Check for explicit auth_type in config
        auth_type = getattr(self.config, "auth_type", None)

        if self._is_cloud:
            # Jira Cloud: Always use Basic Auth with email + API token
            self.auth = HTTPBasicAuth(self.config.username, self.config.api_token)
            self._session.auth = self.auth
            self.logger.info("Using Basic Auth for Jira Cloud")
            return

        # Jira Server/Data Center
        # Check explicit auth_type first
        if auth_type and auth_type.lower() == "bearer":
            self._use_bearer_auth()
            return

        if auth_type and auth_type.lower() == "basic":
            self._use_basic_auth()
            return

        # Auto-detect: If username is provided, use Basic Auth; otherwise use Bearer
        if self.config.username and self.config.username.strip():
            self._use_basic_auth()
        else:
            self._use_bearer_auth()

    def _use_basic_auth(self) -> None:
        """Configure Basic Auth with username and password/token."""
        self.auth = HTTPBasicAuth(self.config.username, self.config.api_token)
        self._session.auth = self.auth
        self.logger.info("Using Basic Auth for Jira Server (username + password/token)")

    def _use_bearer_auth(self) -> None:
        """Configure Bearer token authentication for PAT."""
        self.auth = None
        self._session.auth = None
        self._session.headers["Authorization"] = f"Bearer {self.config.api_token}"
        self.logger.info("Using Bearer Token (PAT) for Jira Server")

    def _detect_api_version(self) -> str:
        """
        Detect whether this is Jira Cloud (v3) or Server/Data Center (v2).

        Uses config.api_version if explicitly set, otherwise auto-detects.
        Jira Cloud URLs typically contain 'atlassian.net'.
        Self-hosted Jira Server/Data Center uses v2.

        Returns:
            API version string ('3' for Cloud, '2' for Server)
        """
        # Use explicit config if set
        if hasattr(self.config, "api_version") and self.config.api_version:
            version = self.config.api_version
            self.logger.info(f"Using configured Jira REST API v{version}")
            return version

        # Auto-detect based on URL
        if self._is_cloud:
            self.logger.info("Detected Jira Cloud - using REST API v3")
            return "3"
        else:
            self.logger.info("Detected Jira Server/Data Center - using REST API v2")
            return "2"

    @property
    def api_base(self) -> str:
        """Get the base API URL for the detected Jira version."""
        return f"{self.base_url}/rest/api/{self._api_version}"

    def register_webhook(
        self,
        webhook_url: str,
        events: list[str] | None = None,
        jql_filter: str | None = None,
        name: str = "AI Orchestrator Webhook",
    ) -> dict[str, Any]:
        """
        Register a webhook in Jira.

        Note: Webhook registration differs between Jira Cloud and Server:
        - Jira Cloud: Uses /rest/api/3/webhook (or webhooks admin)
        - Jira Server: May require manual webhook setup via admin UI

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

        # Webhook payload format
        payload: dict[str, Any] = {
            "name": name,
            "url": webhook_url,
            "events": events,
            "excludeBody": False,
        }

        if jql_filter:
            payload["jqlFilter"] = jql_filter

        # Use the detected API version
        url = f"{self.api_base}/webhook"

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
            # For Jira Server, webhook registration via API might not be available
            if self._api_version == "2" and e.response.status_code in (403, 404):
                self.logger.warning(
                    "Webhook registration via API may not be available on Jira Server. "
                    "Please configure webhooks manually via Jira Administration > System > WebHooks."
                )
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
            # Use the detected API version
            url = f"{self.api_base}/myself"
            self.logger.debug(f"Testing Jira connection to: {url}")
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            user_info = response.json()
            display_name = user_info.get("displayName") or user_info.get("name", "unknown")
            self.logger.info(f"Successfully connected to Jira as: {display_name}")
            return True
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Failed to connect to Jira: {e}", exc_info=True)
            # Try to get response body for more details
            error_body = ""
            try:
                error_body = e.response.text[:500] if e.response.text else ""
            except Exception:
                pass

            # Provide helpful troubleshooting info based on status code
            if e.response.status_code == 401:
                self.logger.error(
                    "401 Unauthorized - Authentication failed.\n"
                    "Troubleshooting steps:\n"
                    "  1. Check JIRA_USERNAME and JIRA_API_TOKEN are correct\n"
                    "  2. For Jira Server with password: set JIRA_AUTH_TYPE=basic\n"
                    "  3. For Jira Server with PAT: set JIRA_AUTH_TYPE=bearer and leave JIRA_USERNAME empty\n"
                    "  4. Try logging into Jira web UI to clear any CAPTCHA"
                )
            elif e.response.status_code == 403:
                self.logger.error(
                    "403 Forbidden - Access denied. This commonly happens because:\n"
                    "  1. Personal Access Tokens (PAT) are not enabled on Jira Server.\n"
                    "     Ask your admin to add JVM parameter: -Datlassian.pats.invalidate.session.enabled=false\n"
                    "  2. Jira Server version is older than 8.14 (PATs require 8.14+)\n"
                    "  3. CAPTCHA was triggered - log into Jira web UI to clear it\n"
                    "  4. REST API access is disabled in Jira security settings\n"
                    "  5. User lacks permissions for REST API access\n"
                    "  6. Try with JIRA_AUTH_TYPE=basic and use password instead of PAT"
                )
                if error_body:
                    self.logger.error(f"Response body: {error_body}")
            elif e.response.status_code == 404:
                self.logger.error(
                    f"404 Not Found - The API endpoint was not found at {url}\n"
                    "  Check that JIRA_URL is correct and Jira is accessible"
                )
            else:
                self.logger.error(f"HTTP {e.response.status_code} error")
                if error_body:
                    self.logger.error(f"Response body: {error_body}")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(
                f"Connection failed to Jira at {self.base_url}: {e}\n"
                "  Check that JIRA_URL is correct and the server is accessible"
            )
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to connect to Jira: {e}", exc_info=True)
            return False

