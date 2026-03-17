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

    def _mock_response(self, endpoint: str, method: str, data: Optional[dict] = None) -> dict:
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

        # Get circles list
        if endpoint == "/circles" and method == "GET":
            return [
                {"id": 1, "name": "AI 课程项目", "description": "学习人工智能的课程项目圈子", "category": "Course", "creator_id": 1},
                {"id": 2, "name": "前端开发", "description": "交流前端技术，包括 React、Vue 等", "category": "Interest", "creator_id": 2},
                {"id": 3, "name": "后端架构", "description": "后端系统设计和架构讨论", "category": "Interest", "creator_id": 1},
                {"id": 4, "name": "算法竞赛", "description": "算法竞赛训练和问题讨论", "category": "Event", "creator_id": 3},
                {"id": 5, "name": "开源社区", "description": "开源项目贡献者社区", "category": "Community", "creator_id": 2},
            ]

        # Create circle
        if endpoint == "/circles" and method == "POST":
            return {
                "id": 6,
                "name": data.get("name", "新圈子") if data else "新圈子",
                "description": data.get("description", "") if data else "",
                "category": data.get("category", "General") if data else "General",
                "creator_id": st.session_state.get("user_id", 1)
            }

        # Get circle detail
        if endpoint.startswith("/circles/") and endpoint.endswith("/join") == False and endpoint.endswith("/leave") == False and method == "GET":
            import re
            match = re.match(r"/circles/(\d+)", endpoint)
            if match:
                circle_id = int(match.group(1))
                circles_map = {
                    1: {"id": 1, "name": "AI 课程项目", "description": "学习人工智能的课程项目圈子", "category": "Course", "creator_id": 1},
                    2: {"id": 2, "name": "前端开发", "description": "交流前端技术，包括 React、Vue 等", "category": "Interest", "creator_id": 2},
                    3: {"id": 3, "name": "后端架构", "description": "后端系统设计和架构讨论", "category": "Interest", "creator_id": 1},
                    4: {"id": 4, "name": "算法竞赛", "description": "算法竞赛训练和问题讨论", "category": "Event", "creator_id": 3},
                    5: {"id": 5, "name": "开源社区", "description": "开源项目贡献者社区", "category": "Community", "creator_id": 2},
                }
                return circles_map.get(circle_id, {"id": circle_id, "name": "圈子详情", "description": "圈子描述", "category": "General", "creator_id": 1})

        # Join circle
        if endpoint.startswith("/circles/") and endpoint.endswith("/join") and method == "POST":
            import re
            match = re.match(r"/circles/(\d+)/join", endpoint)
            if match:
                circle_id = int(match.group(1))
                if "joined_circles" not in st.session_state:
                    st.session_state.joined_circles = []
                if circle_id not in st.session_state.joined_circles:
                    st.session_state.joined_circles.append(circle_id)
                return {"success": True, "message": "Successfully joined the circle", "circle_id": circle_id}

        # Leave circle
        if endpoint.startswith("/circles/") and endpoint.endswith("/leave") and method == "DELETE":
            import re
            match = re.match(r"/circles/(\d+)/leave", endpoint)
            if match:
                circle_id = int(match.group(1))
                if "joined_circles" in st.session_state and circle_id in st.session_state.joined_circles:
                    st.session_state.joined_circles.remove(circle_id)
                return {"success": True, "message": "Successfully left the circle", "circle_id": circle_id}

        # Get circle members
        if endpoint.startswith("/circles/") and endpoint.endswith("/members") and method == "GET":
            return [
                {"id": 1, "username": "user1", "email": "user1@example.com"},
                {"id": 2, "username": "user2", "email": "user2@example.com"},
                {"id": 3, "username": "user3", "email": "user3@example.com"},
            ]

        # Get circle tags
        if endpoint.startswith("/circles/") and "/tags" in endpoint and method == "GET":
            import re
            match = re.match(r"/circles/(\d+)/tags", endpoint)
            if match:
                return [
                    {"id": 1, "name": "专业", "type": "text", "required": True, "options": None, "circle_id": int(match.group(1))},
                    {"id": 2, "name": "年级", "type": "select", "required": True, "options": ["大一", "大二", "大三", "大四", "研一", "研二", "研三"], "circle_id": int(match.group(1))},
                    {"id": 3, "name": "兴趣方向", "type": "multiselect", "required": False, "options": ["机器学习", "计算机视觉", "自然语言处理", "强化学习"], "circle_id": int(match.group(1))},
                ]

        # Default success
        return {"success": True}

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None
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

    def get(self, endpoint: str, params: Optional[dict] = None) -> requests.Response:
        """GET request."""
        return self.request("GET", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> requests.Response:
        """POST request."""
        return self.request("POST", endpoint, data=data, params=params)

    def put(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> requests.Response:
        """PUT request."""
        return self.request("PUT", endpoint, data=data, params=params)

    def delete(self, endpoint: str, params: Optional[dict] = None) -> requests.Response:
        """DELETE request."""
        return self.request("DELETE", endpoint, params=params)


# Singleton instance
api_client = APIClient()
