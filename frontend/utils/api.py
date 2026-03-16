"""
API Client for Boundary Circle Frontend

Supports MOCK_MODE for development without backend.
"""

import os
from typing import Optional

import json
import requests
import streamlit as st

# Configuration
BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
MOCK_MODE = os.environ.get("MOCK_MODE", "true").lower() == "true"


class APIClient:
    """HTTP client for API calls with token management and mock support."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.mock_mode = MOCK_MODE

    def _get_token(self) -> Optional[str]:
        """Get token from session state."""
        return st.session_state.get("access_token")

    def _get_headers(self) -> dict:
        """Build request headers with optional token."""
        headers = {"Content-Type": "application/json"}
        token = self._get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _mock_response(self, endpoint: str, method: str, data: dict = None) -> dict:
        """Generate mock response matching real API format."""

        # Login response
        if endpoint == "/auth/login" and method == "POST":
            username = data.get("username", "user") if data else "user"
            derived_username = username.split("@")[0]
            return {
                "access_token": f"mock_token_{username}",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "username": derived_username,
                    "email": username,
                },
            }

        # Register response (UserRead format)
        if endpoint == "/auth/register" and method == "POST":
            username = data.get("username", "user") if data else "user"
            email = data.get("email", "user@example.com") if data else "user@example.com"
            return {
                "id": 1,
                "username": username,
                "email": email
            }

        # Get current user
        if endpoint == "/auth/me" and method == "GET":
            return {
                "id": st.session_state.get("user_id", 1),
                "username": st.session_state.get("username", "user"),
                "email": st.session_state.get("email", "user@example.com")
            }

        # Default success
        return {"success": True}

    def request(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
        params: dict = None
    ) -> requests.Response:
        """Make HTTP request with token support."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        if self.mock_mode:
            mock_data = self._mock_response(endpoint, method, data)
            response = requests.Response()
            response.status_code = 200
            response._content = json.dumps(mock_data).encode("utf-8")
            response.headers["Content-Type"] = "application/json"
            response.url = url
            response.reason = "OK"
            response.request = requests.Request(method=method, url=url).prepare()
            return response

        return requests.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=headers
        )

    def get(self, endpoint: str, params: dict = None) -> requests.Response:
        """GET request."""
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: dict = None) -> requests.Response:
        """POST request."""
        return self.request("POST", endpoint, data=data)

    def put(self, endpoint: str, data: dict = None) -> requests.Response:
        """PUT request."""
        return self.request("PUT", endpoint, data=data)

    def delete(self, endpoint: str) -> requests.Response:
        """DELETE request."""
        return self.request("DELETE", endpoint)


# Singleton instance
api_client = APIClient()
