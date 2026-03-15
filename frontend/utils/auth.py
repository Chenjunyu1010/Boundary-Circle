"""
Authentication utilities for Boundary Circle Frontend

Provides session management and authentication state handling.
"""

import streamlit as st

from .api import api_client


def init_session_state():
    """Initialize session state variables for authentication."""
    defaults = {
        "logged_in": False,
        "access_token": None,
        "user_id": None,
        "username": None,
        "email": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def is_authenticated() -> bool:
    """Check if user is logged in."""
    return st.session_state.get("logged_in", False)


def get_current_user() -> dict:
    """Get current user information."""
    if not is_authenticated():
        return {}

    return {
        "id": st.session_state.get("user_id"),
        "username": st.session_state.get("username"),
        "email": st.session_state.get("email"),
    }


def _fetch_user_info() -> bool:
    """
    Fetch user info from /auth/me endpoint after login.
    Returns True if successful, False otherwise.
    """
    try:
        response = api_client.get("/auth/me")
        if response.ok:
            data = response.json()
            st.session_state.user_id = data.get("id")
            st.session_state.username = data.get("username")
            st.session_state.email = data.get("email")
            return True
    except Exception:
        pass
    return False


def login(email: str, password: str) -> tuple[bool, str]:
    """Attempt to log in user."""
    try:
        response = api_client.post(
            "/auth/login",
            data={"username": email, "password": password}
        )

        if response.ok:
            data = response.json()
            st.session_state.access_token = data.get("access_token")

            if api_client.mock_mode:
                user = data.get("user", {})
                st.session_state.user_id = user.get("id", 1)
                st.session_state.username = user.get("username", email.split("@")[0])
                st.session_state.email = user.get("email", email)
                st.session_state.logged_in = True
            else:
                if not _fetch_user_info():
                    st.session_state.access_token = None
                    st.session_state.logged_in = False
                    st.session_state.user_id = None
                    st.session_state.username = None
                    st.session_state.email = None
                    return False, "Login failed: unable to load user profile."
                st.session_state.logged_in = True

            return True, "Login successful!"

        else:
            error_msg = getattr(response, "reason", "Login failed")
            return False, f"Login failed: {error_msg}"

    except Exception as e:
        return False, f"Network error: {str(e)}"


def register(username: str, email: str, password: str) -> tuple[bool, str]:
    """Attempt to register new user."""
    try:
        response = api_client.post(
            "/auth/register",
            data={
                "username": username,
                "email": email,
                "password": password
            }
        )

        if response.ok:
            data = response.json()
            st.session_state.user_id = data.get("id")
            st.session_state.username = data.get("username")
            st.session_state.email = data.get("email")

            return True, "Registration successful! Please login."

        else:
            error_msg = getattr(response, "reason", "Registration failed")
            return False, f"Registration failed: {error_msg}"

    except Exception as e:
        return False, f"Network error: {str(e)}"


def logout():
    """Log out current user and clear session state."""
    st.session_state.logged_in = False
    st.session_state.access_token = None
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.email = None


def require_auth():
    """Decorator-like function to require authentication."""
    if not is_authenticated():
        st.warning("Please login to access this page")
        st.stop()
