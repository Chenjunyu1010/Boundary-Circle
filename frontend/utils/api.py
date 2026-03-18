"""
API client for Boundary Circle frontend.

Supports MOCK_MODE so the Streamlit pages can be exercised without a backend.
"""

import json
import os
from typing import Optional

import requests
import streamlit as st


BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
MOCK_MODE = os.environ.get("MOCK_MODE", "true").lower() == "true"


class APIClient:
    """HTTP client with optional mock responses."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.mock_mode = MOCK_MODE

    def _get_token(self) -> Optional[str]:
        """Get access token from session state."""
        return st.session_state.get("access_token")

    def _get_headers(self) -> dict:
        """Build request headers."""
        headers = {"Content-Type": "application/json"}
        token = self._get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _get_mock_circles(self) -> list[dict]:
        """Return default circles."""
        return [
            {
                "id": 1,
                "name": "AI Course Project",
                "description": "Find teammates for the course project.",
                "category": "Course",
                "creator_id": 1,
            },
            {
                "id": 2,
                "name": "Frontend Studio",
                "description": "Discuss frontend patterns and polish UI.",
                "category": "Interest",
                "creator_id": 2,
            },
            {
                "id": 3,
                "name": "Backend Architecture",
                "description": "Design APIs, schemas, and services.",
                "category": "Interest",
                "creator_id": 1,
            },
            {
                "id": 4,
                "name": "Algorithm Sprint",
                "description": "Practice contest problems together.",
                "category": "Event",
                "creator_id": 3,
            },
            {
                "id": 5,
                "name": "Open Source Club",
                "description": "Collaborate on open source contributions.",
                "category": "Community",
                "creator_id": 2,
            },
        ]

    def _get_mock_tags(self, circle_id: int) -> list[dict]:
        """Return tag definitions for a circle."""
        return [
            {
                "id": 1,
                "name": "Major",
                "type": "text",
                "required": True,
                "options": None,
                "circle_id": circle_id,
            },
            {
                "id": 2,
                "name": "Grade",
                "type": "select",
                "required": True,
                "options": ["Freshman", "Sophomore", "Junior", "Senior"],
                "circle_id": circle_id,
            },
            {
                "id": 3,
                "name": "Interest",
                "type": "multiselect",
                "required": False,
                "options": ["AI", "Vision", "NLP", "Backend", "Frontend"],
                "circle_id": circle_id,
            },
        ]

    def _get_mock_members(self, circle_id: int) -> list[dict]:
        """Return circle members for mock mode."""
        return [
            {"id": 1, "username": "alice", "email": "alice@example.com", "circle_id": circle_id},
            {"id": 2, "username": "bob", "email": "bob@example.com", "circle_id": circle_id},
            {"id": 3, "username": "carol", "email": "carol@example.com", "circle_id": circle_id},
            {"id": 4, "username": "dave", "email": "dave@example.com", "circle_id": circle_id},
            {"id": 5, "username": "erin", "email": "erin@example.com", "circle_id": circle_id},
        ]

    def _ensure_mock_teams(self, circle_id: int) -> list[dict]:
        """Return mutable team state for a circle."""
        if "mock_teams" not in st.session_state:
            st.session_state.mock_teams = {}

        if circle_id not in st.session_state.mock_teams:
            st.session_state.mock_teams[circle_id] = [
                {
                    "id": 1,
                    "name": "AI Pioneer Team",
                    "description": "Build AI features together.",
                    "max_members": 5,
                    "current_members": 2,
                    "status": "Recruiting",
                    "creator_id": 1,
                    "circle_id": circle_id,
                    "required_tags": ["skill", "availability"],
                    "member_ids": [1, 2],
                },
                {
                    "id": 2,
                    "name": "Backend Guild",
                    "description": "Design APIs and data models.",
                    "max_members": 4,
                    "current_members": 4,
                    "status": "Locked",
                    "creator_id": 2,
                    "circle_id": circle_id,
                    "required_tags": ["role"],
                    "member_ids": [2, 3, 4, 5],
                },
            ]

        return st.session_state.mock_teams[circle_id]

    def _ensure_mock_invitations(self) -> list[dict]:
        """Return mutable invitation state."""
        if "mock_invitations" not in st.session_state:
            st.session_state.mock_invitations = [
                {
                    "id": 1,
                    "team_id": 1,
                    "circle_id": 1,
                    "team_name": "AI Pioneer Team",
                    "inviter_id": 1,
                    "invitee_id": 2,
                    "status": "pending",
                }
            ]
        return st.session_state.mock_invitations

    def _find_mock_team(self, team_id: int) -> Optional[dict]:
        """Find a team by id across circles."""
        mock_teams = st.session_state.get("mock_teams", {})
        for teams in mock_teams.values():
            for team in teams:
                if team.get("id") == team_id:
                    return team
        return None

    def _create_mock_response(self, url: str, payload) -> requests.Response:
        """Wrap a mock payload in a requests.Response.

        Attempts to map common failure payloads (e.g. {"success": False, "message": ...})
        to appropriate HTTP status codes so that response.ok and status_code behave
        similarly to a real backend.
        """
        response = requests.Response()

        # Default to HTTP 200 OK.
        status_code = 200
        reason = "OK"

        # If the payload explicitly indicates failure, derive a more specific status.
        if isinstance(payload, dict) and payload.get("success") is False:
            message = str(payload.get("message", "")).lower()
            # Default failure is treated as a 400 Bad Request.
            status_code = 400
            reason = "Bad Request"

            # Heuristic mapping based on common error messages used in the mock layer.
            if "not found" in message:
                status_code = 404
                reason = "Not Found"
            elif "already" in message or "duplicate" in message or "exists" in message:
                status_code = 409
                reason = "Conflict"

        response.status_code = status_code
        response._content = json.dumps(payload).encode("utf-8")
        response.headers["Content-Type"] = "application/json"
        response.url = url
        response.reason = reason
        response.request = requests.Request(method="MOCK", url=url).prepare()
        return response

    def _mock_response(self, endpoint: str, method: str, data: Optional[dict] = None):
        """Generate mock response matching the backend contract."""
        if endpoint == "/auth/login" and method == "POST":
            username = data.get("username", "user@example.com") if data else "user@example.com"
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

        if endpoint == "/auth/register" and method == "POST":
            return {
                "id": 1,
                "username": data.get("username", "user") if data else "user",
                "email": data.get("email", "user@example.com") if data else "user@example.com",
            }

        if endpoint == "/auth/me" and method == "GET":
            return {
                "id": st.session_state.get("user_id", 1),
                "username": st.session_state.get("username", "user"),
                "email": st.session_state.get("email", "user@example.com"),
            }

        if endpoint == "/circles" and method == "GET":
            return self._get_mock_circles()

        if endpoint == "/circles" and method == "POST":
            creator_id = st.session_state.get("user_id", 1)
            return {
                "id": 6,
                "name": data.get("name", "New Circle") if data else "New Circle",
                "description": data.get("description", "") if data else "",
                "category": data.get("category", "General") if data else "General",
                "creator_id": creator_id,
            }

        if endpoint.startswith("/circles/") and method == "GET" and not endpoint.endswith("/join") and not endpoint.endswith("/leave"):
            import re

            if endpoint.endswith("/members"):
                match = re.match(r"/circles/(\d+)/members", endpoint)
                if match:
                    return self._get_mock_members(int(match.group(1)))

            if "/tags" in endpoint:
                match = re.match(r"/circles/(\d+)/tags", endpoint)
                if match:
                    return self._get_mock_tags(int(match.group(1)))

            if "/teams" in endpoint:
                match = re.match(r"/circles/(\d+)/teams", endpoint)
                if match:
                    return self._ensure_mock_teams(int(match.group(1)))

            match = re.match(r"/circles/(\d+)", endpoint)
            if match:
                circle_id = int(match.group(1))
                circles = {circle["id"]: circle for circle in self._get_mock_circles()}
                return circles.get(
                    circle_id,
                    {
                        "id": circle_id,
                        "name": "Circle Detail",
                        "description": "Mock circle detail page.",
                        "category": "General",
                        "creator_id": 1,
                    },
                )

        if endpoint.startswith("/circles/") and endpoint.endswith("/join") and method == "POST":
            import re

            match = re.match(r"/circles/(\d+)/join", endpoint)
            if match:
                circle_id = int(match.group(1))
                joined_circles = st.session_state.setdefault("joined_circles", [])
                if circle_id not in joined_circles:
                    joined_circles.append(circle_id)
                return {"success": True, "message": "Successfully joined the circle", "circle_id": circle_id}

        if endpoint.startswith("/circles/") and endpoint.endswith("/leave") and method == "DELETE":
            import re

            match = re.match(r"/circles/(\d+)/leave", endpoint)
            if match:
                circle_id = int(match.group(1))
                joined_circles = st.session_state.get("joined_circles", [])
                if circle_id in joined_circles:
                    joined_circles.remove(circle_id)
                return {"success": True, "message": "Successfully left the circle", "circle_id": circle_id}

        def _get_next_mock_team_id():
            """Generate a globally unique mock team ID across all circles."""
            if "mock_next_team_id" not in st.session_state:
                max_id = 0
                # Best-effort scan for existing team-like dicts with an 'id' key
                for value in st.session_state.values():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict) and "id" in item:
                                try:
                                    item_id = int(item["id"])
                                except (TypeError, ValueError):
                                    continue
                                if item_id > max_id:
                                    max_id = item_id
                st.session_state["mock_next_team_id"] = max_id + 1
            next_id = st.session_state["mock_next_team_id"]
            st.session_state["mock_next_team_id"] = next_id + 1
            return next_id

        def _get_next_mock_team_id():
            """Generate a globally unique mock team ID across all circles."""
            if "mock_next_team_id" not in st.session_state:
                max_id = 0
            team_id = _get_next_mock_team_id()
                for value in st.session_state.values():
                "id": team_id,
                        for item in value:
                            if isinstance(item, dict) and "id" in item:
                                try:
                                    item_id = int(item["id"])
                                except (TypeError, ValueError):
                                    continue
                                if item_id > max_id:
                                    max_id = item_id
                st.session_state["mock_next_team_id"] = max_id + 1
            next_id = st.session_state["mock_next_team_id"]
            st.session_state["mock_next_team_id"] = next_id + 1
            return next_id

        if endpoint == "/teams" and method == "POST":
            circle_id = data.get("circle_id", 1) if data else 1
            creator_id = st.session_state.get("user_id", 1)
            teams = self._ensure_mock_teams(circle_id)
            team_id = _get_next_mock_team_id()
            team = {
                "id": team_id,
                "name": data.get("name", "New Team") if data else "New Team",
                "description": data.get("description", "") if data else "",
                "max_members": data.get("max_members", 5) if data else 5,
                "current_members": 1,
                "status": "Recruiting",
                "creator_id": creator_id,
                "circle_id": circle_id,
                "required_tags": data.get("required_tags", []) if data else [],
                "member_ids": [creator_id],
            }
            teams.append(team)
            return team

        if endpoint.startswith("/teams/") and endpoint.endswith("/invite") and method == "POST":
            import re

            match = re.match(r"/teams/(\d+)/invite", endpoint)
            if match and data:
                team_id = int(match.group(1))
                team = self._find_mock_team(team_id)
                invitations = self._ensure_mock_invitations()
                invitee_id = data.get("user_id")

                if team is None:
                    return {"success": False, "message": "Team not found"}
                if invitee_id in team.get("member_ids", []):
                    return {"success": False, "message": "User is already a team member"}

                existing_pending = next(
                    (
                        invite
                        for invite in invitations
                        if invite.get("team_id") == team_id
                        and invite.get("invitee_id") == invitee_id
                        and invite.get("status") == "pending"
                    ),
                    None,
                )
                if existing_pending is not None:
                    return {"success": False, "message": "Invitation already pending"}

                new_invitation = {
                    "id": max((invite.get("id", 0) for invite in invitations), default=0) + 1,
                    "team_id": team_id,
                    "circle_id": team.get("circle_id"),
                    "team_name": data.get("team_name", team.get("name", "Team")),
                    "inviter_id": st.session_state.get("user_id", 1),
                    "invitee_id": invitee_id,
                    "status": "pending",
                }
                invitations.append(new_invitation)
                return new_invitation

        if endpoint == "/invitations" and method == "GET":
            invitations = self._ensure_mock_invitations()
            user_id = st.session_state.get("user_id", 1)
            return [
                invite
                for invite in invitations
                if invite.get("invitee_id") == user_id or invite.get("inviter_id") == user_id
            ]

        if endpoint.startswith("/invitations/") and endpoint.endswith("/respond") and method == "POST":
            import re

            match = re.match(r"/invitations/(\d+)/respond", endpoint)
            if match and data:
                invite_id = int(match.group(1))
                accept = bool(data.get("accept", False))
                invitations = self._ensure_mock_invitations()
                for invitation in invitations:
                    if invitation.get("id") != invite_id:
                        continue

                    invitation["status"] = "accepted" if accept else "rejected"
                    if accept:
                        team = self._find_mock_team(invitation.get("team_id"))
                        invitee_id = invitation.get("invitee_id")
                        if team is not None and invitee_id is not None:
                            member_ids = team.setdefault("member_ids", [])
                            if invitee_id not in member_ids:
                                member_ids.append(invitee_id)
                            team["current_members"] = len(member_ids)
                            team["status"] = (
                                "Locked"
                                if team["current_members"] >= team.get("max_members", 0)
                                else "Recruiting"
                            )
                    return {
                        "success": True,
                        "message": "Invitation accepted" if accept else "Invitation rejected",
                    }

            return {"success": False, "message": "Invalid request"}

        return {"success": True}

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> requests.Response:
        """Make an HTTP request."""
        url = f"{self.base_url}{endpoint}"

        if self.mock_mode:
            return self._create_mock_response(url, self._mock_response(endpoint, method, data))

        return requests.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=self._get_headers(),
        )

    def get(self, endpoint: str, params: Optional[dict] = None) -> requests.Response:
        """Perform a GET request."""
        return self.request("GET", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> requests.Response:
        """Perform a POST request."""
        return self.request("POST", endpoint, data=data, params=params)

    def put(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> requests.Response:
        """Perform a PUT request."""
        return self.request("PUT", endpoint, data=data, params=params)

    def delete(self, endpoint: str, params: Optional[dict] = None) -> requests.Response:
        """Perform a DELETE request."""
        return self.request("DELETE", endpoint, params=params)


api_client = APIClient()
