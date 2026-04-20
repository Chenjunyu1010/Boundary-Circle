"""
API client for Boundary Circle frontend.

Uses the real backend API by default, with optional mock mode for development/tests.
"""

import json
import os
from typing import Any, Optional

import requests
import streamlit as st


def _get_config_value(name: str, default: str) -> str:
    """Read config from environment first, then Streamlit secrets."""
    env_value = os.environ.get(name)
    if env_value:
        return env_value

    try:
        secrets = getattr(st, "secrets", {})
        value = secrets.get(name)
    except Exception:
        value = None

    return str(value) if value is not None else default


BASE_URL = _get_config_value("API_BASE_URL", "http://127.0.0.1:8000")
MOCK_MODE = _get_config_value("MOCK_MODE", "false").lower() == "true"


class APIClient:
    """HTTP client with optional mock responses."""

    def __init__(self):
        self.base_url = BASE_URL
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

    def _ensure_mock_circles(self) -> list[dict]:
        """Return mutable mock circles stored in session state."""
        if "mock_circles" not in st.session_state:
            st.session_state.mock_circles = [
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
        return st.session_state.mock_circles

    def _get_mock_tags(self, circle_id: int) -> list[dict]:
        """Return tag definitions for a circle."""
        return [
            {
                "id": 1,
                "name": "Major",
                "data_type": "single_select",
                "required": True,
                "options": ["Artificial Intelligence", "Computer Science", "Software Engineering"],
                "circle_id": circle_id,
            },
            {
                "id": 2,
                "name": "Weekly Hours",
                "data_type": "integer",
                "required": True,
                "options": None,
                "circle_id": circle_id,
            },
            {
                "id": 3,
                "name": "Tech Stack",
                "data_type": "multi_select",
                "required": False,
                "options": ["Python", "Java", "React", "SQL", "FastAPI"],
                "max_selections": 3,
                "circle_id": circle_id,
            },
            {
                "id": 4,
                "name": "Remote OK",
                "data_type": "boolean",
                "required": False,
                "options": None,
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
                    "inviter_username": "alice",
                    "invitee_id": 2,
                    "invitee_username": "bob",
                    "kind": "invite",
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

        status_code = 200
        reason = "OK"

        if isinstance(payload, dict) and payload.get("success") is False:
            message = str(payload.get("message", "")).lower()
            status_code = 400
            reason = "Bad Request"

            if "not found" in message:
                status_code = 404
                reason = "Not Found"
            elif "only" in message and "respond" in message:
                status_code = 403
                reason = "Forbidden"
            elif "already" in message or "duplicate" in message or "exists" in message:
                status_code = 409
                reason = "Conflict"
        elif (
            isinstance(payload, dict)
            and payload.get("id") is not None
            and payload.get("team_id") is not None
            and payload.get("status") == "pending"
        ):
            status_code = 201
            reason = "Created"

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
                "full_name": st.session_state.get("full_name"),
            }

        if endpoint == "/profile/me" and method == "GET":
            if "mock_profile" not in st.session_state:
                st.session_state.mock_profile = {
                    "id": st.session_state.get("user_id", 1),
                    "username": st.session_state.get("username", "user"),
                    "email": st.session_state.get("email", "user@example.com"),
                    "full_name": st.session_state.get("full_name"),
                    "gender": None,
                    "birthday": None,
                    "bio": None,
                    "profile_prompt_dismissed": False,
                    "show_full_name": True,
                    "show_gender": True,
                    "show_birthday": True,
                    "show_email": True,
                    "show_bio": True,
                }
            return st.session_state.mock_profile

        if endpoint == "/profile/me" and method == "PUT":
            profile = dict(self._mock_response("/profile/me", "GET"))
            if data:
                profile.update(data)
                if "full_name" in data:
                    st.session_state.full_name = data.get("full_name")
            st.session_state.mock_profile = profile
            return profile

        if endpoint == "/profile/me/dismiss-prompt" and method == "POST":
            profile = dict(self._mock_response("/profile/me", "GET"))
            profile["profile_prompt_dismissed"] = True
            st.session_state.mock_profile = profile
            return profile

        if endpoint.startswith("/users/") and endpoint.endswith("/profile") and method == "GET":
            import re

            match = re.match(r"/users/(\d+)/profile", endpoint)
            if match:
                user_id = int(match.group(1))
                mock_members = self._get_mock_members(circle_id=1)
                member = next(
                    (item for item in mock_members if item.get("id") == user_id),
                    None,
                )
                if member is None:
                    return {
                        "success": False,
                        "message": "User not found",
                        "detail": "User not found",
                    }

                return {
                    "id": user_id,
                    "username": member.get("username", f"user{user_id}"),
                    "email": member.get("email"),
                    "full_name": f"{member.get('username', 'User').title()} Example",
                    "gender": None,
                    "birthday": None,
                    "bio": f"Public bio for {member.get('username', 'this user')}.",
                }

        if endpoint == "/circles" and method == "GET":
            return self._ensure_mock_circles()

        if endpoint == "/circles" and method == "POST":
            circles = self._ensure_mock_circles()
            next_circle_id = max((circle.get("id", 0) for circle in circles), default=0) + 1
            creator_id = st.session_state.get("user_id", 1)
            new_circle = {
                "id": next_circle_id,
                "name": data.get("name", "New Circle") if data else "New Circle",
                "description": data.get("description", "") if data else "",
                "category": data.get("category", "General") if data else "General",
                "creator_id": creator_id,
            }
            circles.append(new_circle)
            return new_circle

        if (
            endpoint.startswith("/circles/")
            and method == "GET"
            and not endpoint.endswith("/join")
            and not endpoint.endswith("/leave")
        ):
            import re

            if endpoint.endswith("/members"):
                match = re.match(r"/circles/(\d+)/members", endpoint)
                if match:
                    return self._get_mock_members(int(match.group(1)))

            if "/tags" in endpoint:
                member_tags_match = re.match(r"/circles/(\d+)/members/(\d+)/tags", endpoint)
                if member_tags_match:
                    circle_id = int(member_tags_match.group(1))
                    user_id = int(member_tags_match.group(2))
                    mock_tags = self._get_mock_tags(circle_id)
                    sample_values = {
                        1: {
                            "Major": "Artificial Intelligence",
                            "Weekly Hours": "10",
                            "Tech Stack": '["Python", "React"]',
                            "Remote OK": "true",
                        },
                        2: {
                            "Major": "Computer Science",
                            "Weekly Hours": "8",
                            "Tech Stack": '["Python", "SQL"]',
                            "Remote OK": "false",
                        },
                        3: {
                            "Major": "Software Engineering",
                            "Weekly Hours": "6",
                            "Tech Stack": '["React"]',
                            "Remote OK": "true",
                        },
                        4: {
                            "Major": "Artificial Intelligence",
                            "Weekly Hours": "12",
                            "Tech Stack": '["Python", "SQL"]',
                            "Remote OK": "true",
                        },
                        5: {
                            "Major": "Computer Science",
                            "Weekly Hours": "7",
                            "Tech Stack": '["React", "SQL"]',
                            "Remote OK": "false",
                        },
                    }
                    values = sample_values.get(user_id, {})
                    result = []
                    next_id = 1
                    for tag in mock_tags:
                        tag_name = tag.get("name")
                        if tag_name not in values:
                            continue
                        result.append(
                            {
                                "id": next_id,
                                "user_id": user_id,
                                "circle_id": circle_id,
                                "tag_definition_id": tag.get("id"),
                                "tag_name": tag_name,
                                "data_type": tag.get("data_type"),
                                "value": values[tag_name],
                            }
                        )
                        next_id += 1
                    return result

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
                circles = {circle["id"]: circle for circle in self._ensure_mock_circles()}
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

        def _get_next_mock_team_id() -> int:
            """Generate a globally unique mock team ID across all circles."""
            if "mock_next_team_id" not in st.session_state:
                max_id = 0
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
                    "inviter_username": next(
                        (
                            member.get("username")
                            for member in self._get_mock_members(team.get("circle_id", 1))
                            if member.get("id") == st.session_state.get("user_id", 1)
                        ),
                        None,
                    ),
                    "invitee_id": invitee_id,
                    "invitee_username": next(
                        (
                            member.get("username")
                            for member in self._get_mock_members(team.get("circle_id", 1))
                            if member.get("id") == invitee_id
                        ),
                        None,
                    ),
                    "kind": "invite",
                    "status": "pending",
                }
                invitations.append(new_invitation)
                return new_invitation

        if endpoint.startswith("/teams/") and endpoint.endswith("/request-join") and method == "POST":
            import re

            match = re.match(r"/teams/(\d+)/request-join", endpoint)
            if match:
                team_id = int(match.group(1))
                team = self._find_mock_team(team_id)
                invitations = self._ensure_mock_invitations()
                requester_id = st.session_state.get("user_id", 1)

                if team is None:
                    return {"success": False, "message": "Team not found"}
                if requester_id in team.get("member_ids", []):
                    return {"success": False, "message": "User is already a team member"}
                if team.get("current_members", 0) >= team.get("max_members", 0):
                    return {"success": False, "message": "Team is already full"}

                invitations[:] = [
                    invite
                    for invite in invitations
                    if not (
                        invite.get("team_id") == team_id
                        and invite.get("inviter_id") == requester_id
                        and invite.get("kind") == "join_request"
                        and invite.get("status") == "pending"
                    )
                ]

                circle_members = self._get_mock_members(team.get("circle_id", 1))
                requester_username = next(
                    (member.get("username") for member in circle_members if member.get("id") == requester_id),
                    f"user{requester_id}",
                )
                creator_id = team.get("creator_id", 1)
                creator_username = next(
                    (member.get("username") for member in circle_members if member.get("id") == creator_id),
                    f"user{creator_id}",
                )
                new_request = {
                    "id": max((invite.get("id", 0) for invite in invitations), default=0) + 1,
                    "team_id": team_id,
                    "circle_id": team.get("circle_id"),
                    "team_name": team.get("name", "Team"),
                    "inviter_id": requester_id,
                    "inviter_username": requester_username,
                    "invitee_id": creator_id,
                    "invitee_username": creator_username,
                    "kind": "join_request",
                    "status": "pending",
                }
                invitations.append(new_request)
                return new_request

        if endpoint == "/invitations" and method == "GET":
            invitations = self._ensure_mock_invitations()
            user_id = st.session_state.get("user_id", 1)
            return [
                invite
                for invite in invitations
                if (
                    invite.get("kind", "invite") == "invite"
                    and invite.get("invitee_id") == user_id
                )
                or (
                    invite.get("kind", "invite") == "join_request"
                    and (
                        invite.get("invitee_id") == user_id or invite.get("inviter_id") == user_id
                    )
                )
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

                    kind = invitation.get("kind", "invite")
                    current_user_id = st.session_state.get("user_id", 1)
                    if kind == "join_request" and invitation.get("invitee_id") != current_user_id:
                        return {"success": False, "message": "Only the team creator can respond"}
                    if kind == "invite" and invitation.get("invitee_id") != current_user_id:
                        return {"success": False, "message": "Only the invitee can respond"}

                    invitation["status"] = "accepted" if accept else "rejected"
                    if accept:
                        team = self._find_mock_team(invitation.get("team_id"))
                        joined_user_id = (
                            invitation.get("inviter_id")
                            if kind == "join_request"
                            else invitation.get("invitee_id")
                        )
                        if team is not None and joined_user_id is not None:
                            member_ids = team.setdefault("member_ids", [])
                            if joined_user_id not in member_ids:
                                member_ids.append(joined_user_id)
                            team["current_members"] = len(member_ids)
                            team["status"] = (
                                "Locked"
                                if team["current_members"] >= team.get("max_members", 0)
                                else "Recruiting"
                            )
                    return {
                        "success": True,
                        "message": (
                            "Join request accepted"
                            if kind == "join_request" and accept
                            else "Join request rejected"
                            if kind == "join_request"
                            else "Invitation accepted"
                            if accept
                            else "Invitation rejected"
                        ),
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


def response_json_object(response) -> dict[str, Any]:
    """Return a JSON object payload or an empty dict for non-object payloads."""
    try:
        payload = response.json()
    except Exception:
        return {}

    return payload if isinstance(payload, dict) else {}
