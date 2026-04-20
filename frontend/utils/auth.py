"""
Authentication utilities for Boundary Circle Frontend

Provides session management and authentication state handling.
"""

import streamlit as st
import logging
from typing import Optional

from .api import api_client, response_json_object


AUTH_COOKIE_NAME = "boundary_circle_access_token"
AUTH_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
AUTH_BRIDGE_FLAG = "boundary_circle_auth_bridge_ran"


def _clear_auth_session() -> None:
    st.session_state.logged_in = False
    st.session_state.access_token = None
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.email = None
    st.session_state.full_name = None
    st.session_state.show_profile_completion_prompt = False


def _sync_auth_cookie(access_token: Optional[str]) -> None:
    try:
        from streamlit.components.v1 import html
    except Exception:
        logging.exception("Failed to import Streamlit components for auth cookie sync")
        return

    script = (
        "<script>"
        "const secure = window.location.protocol === 'https:' ? '; Secure' : '';"
        f"const cookieName = {AUTH_COOKIE_NAME!r};"
        f"const bridgeFlag = {AUTH_BRIDGE_FLAG!r};"
    )
    if access_token:
        script += (
            f"document.cookie = `${{cookieName}}={access_token}; Max-Age={AUTH_COOKIE_MAX_AGE_SECONDS}; Path=/; SameSite=Lax${{secure}}`;"
            f"window.localStorage.setItem(cookieName, {access_token!r});"
        )
    else:
        script += (
            "document.cookie = `${cookieName}=; Max-Age=0; Path=/; SameSite=Lax${secure}`;"
            "window.localStorage.removeItem(cookieName);"
        )
    script += "window.sessionStorage.removeItem(bridgeFlag);</script>"

    html(script, height=0, width=0)


def _get_persisted_access_token() -> Optional[str]:
    cookies = getattr(getattr(st, "context", None), "cookies", None)
    if not cookies:
        return None
    return cookies.get(AUTH_COOKIE_NAME)


def _run_browser_auth_bridge() -> None:
    """Rehydrate the auth cookie from browser storage when Streamlit cannot see it yet."""
    try:
        from streamlit.components.v1 import html
    except Exception:
        logging.exception("Failed to import Streamlit components for auth bridge")
        return

    html(
        (
            "<script>"
            "const secure = window.location.protocol === 'https:' ? '; Secure' : '';"
            f"const cookieName = {AUTH_COOKIE_NAME!r};"
            f"const bridgeFlag = {AUTH_BRIDGE_FLAG!r};"
            "const persistedToken = window.localStorage.getItem(cookieName);"
            "const hasCookie = document.cookie.split('; ').some((item) => item.startsWith(`${cookieName}=`));"
            "if (!persistedToken || hasCookie) {"
            "  window.sessionStorage.removeItem(bridgeFlag);"
            "} else if (!window.sessionStorage.getItem(bridgeFlag)) {"
            "  window.sessionStorage.setItem(bridgeFlag, '1');"
            f"  document.cookie = `${{cookieName}}=${{persistedToken}}; Max-Age={AUTH_COOKIE_MAX_AGE_SECONDS}; Path=/; SameSite=Lax${{secure}}`;"
            "  window.location.reload();"
            "}"
            "</script>"
        ),
        height=0,
        width=0,
    )


def _restore_session_from_persisted_token(persisted_token: str) -> None:
    st.session_state.access_token = persisted_token

    try:
        response = api_client.get("/auth/me")
    except Exception:
        logging.exception("Failed to restore user info from persisted token")
        return

    if response.ok:
        data = response_json_object(response)
        st.session_state.user_id = data.get("id")
        st.session_state.username = data.get("username")
        st.session_state.email = data.get("email")
        st.session_state.full_name = data.get("full_name")
        st.session_state.logged_in = True
        _load_profile_prompt_state()
        return

    if getattr(response, "status_code", None) in (401, 403):
        _clear_auth_session()
        _sync_auth_cookie(None)


def init_session_state():
    """Initialize session state variables for authentication."""
    defaults = {
        "logged_in": False,
        "access_token": None,
        "user_id": None,
        "username": None,
        "email": None,
        "full_name": None,
        "show_profile_completion_prompt": False,
        "_auth_restore_attempted": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if (
        not st.session_state.get("_auth_restore_attempted")
        and not st.session_state.get("logged_in")
        and not st.session_state.get("access_token")
    ):
        st.session_state["_auth_restore_attempted"] = True
        persisted_token = _get_persisted_access_token()
        if persisted_token:
            _restore_session_from_persisted_token(persisted_token)
        else:
            _run_browser_auth_bridge()


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
        "full_name": st.session_state.get("full_name"),
    }


def _fetch_user_info() -> bool:
    """
    Fetch user info from /auth/me endpoint after login.
    Returns True if successful, False otherwise.
    """
    try:
        response = api_client.get("/auth/me")
        if response.ok:
            data = response_json_object(response)
            st.session_state.user_id = data.get("id")
            st.session_state.username = data.get("username")
            st.session_state.email = data.get("email")
            st.session_state.full_name = data.get("full_name")
            return True
    except Exception:
        logging.exception("Failed to fetch user info from /auth/me")
    return False


def _should_prompt_profile_completion(profile: dict) -> bool:
    if profile.get("profile_prompt_dismissed"):
        return False
    return not any(
        [
            profile.get("gender"),
            profile.get("birthday"),
            profile.get("bio"),
        ]
    )


def _load_profile_prompt_state() -> None:
    try:
        response = api_client.get("/profile/me")
        if not response.ok:
            st.session_state.show_profile_completion_prompt = False
            return
        st.session_state.show_profile_completion_prompt = _should_prompt_profile_completion(
            response_json_object(response)
        )
    except Exception:
        logging.exception("Failed to fetch profile onboarding state")
        st.session_state.show_profile_completion_prompt = False


def login(email: str, password: str) -> tuple[bool, str]:
    """Attempt to log in user."""
    try:
        response = api_client.post(
            "/auth/login",
            data={"username": email, "password": password}
        )

        if response.ok:
            data = response_json_object(response)
            access_token = data.get("access_token")
            if not access_token:
                # Treat missing or empty access token as a login failure
                _clear_auth_session()
                return False, "Login failed: invalid authentication response from server."

            st.session_state.access_token = access_token
            _sync_auth_cookie(access_token)

            if api_client.mock_mode:
                user = data.get("user", {})
                st.session_state.user_id = user.get("id", 1)
                st.session_state.username = user.get("username", email.split("@")[0])
                st.session_state.email = user.get("email", email)
                st.session_state.full_name = user.get("full_name")
                st.session_state.logged_in = True
            else:
                if not _fetch_user_info():
                    _clear_auth_session()
                    _sync_auth_cookie(None)
                    return False, "Login failed: unable to load user profile."
                st.session_state.logged_in = True
                _load_profile_prompt_state()

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
            data = response_json_object(response)
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
    _clear_auth_session()
    _sync_auth_cookie(None)


def require_auth():
    """Decorator-like function to require authentication."""
    if not is_authenticated():
        st.warning("Please login to access this page")
        st.stop()
