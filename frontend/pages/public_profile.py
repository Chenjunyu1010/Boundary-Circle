"""
Dedicated page for viewing another user's public profile.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import streamlit as st

parent_dir = str(Path(__file__).resolve().parents[1])
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.api import api_client
from utils.auth import require_auth
from navigation import get_navigation_page


def build_avatar_text(username: Optional[str]) -> str:
    if not username:
        return "U"
    compact = "".join(ch for ch in username.strip() if not ch.isspace())
    if not compact:
        return "U"
    return compact[:2].upper()


def parse_user_id(raw_value) -> Optional[int]:
    if isinstance(raw_value, list):
        raw_value = raw_value[0] if raw_value else None
    if raw_value in (None, ""):
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


def get_target_user_id() -> Optional[int]:
    session_user_id = parse_user_id(st.session_state.get("public_profile_target_user_id"))
    if session_user_id is not None:
        return session_user_id
    return parse_user_id(st.query_params.get("user_id"))


def load_public_profile(user_id: int) -> Optional[dict]:
    response = api_client.get(f"/users/{user_id}/profile")
    if not response.ok:
        detail = getattr(response, "reason", "Unknown error")
        try:
            detail = response.json().get("detail", detail)
        except Exception:
            pass
        st.error(f"Failed to load public profile: {detail}")
        return None
    return response.json()


def build_public_profile_rows(profile: dict) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = [("Username", profile.get("username", "Unknown"))]
    optional_fields = [
        ("Full name", profile.get("full_name")),
        ("Email", profile.get("email")),
        ("Gender", profile.get("gender")),
        ("Birthday", profile.get("birthday")),
        ("Bio", profile.get("bio")),
    ]
    rows.extend((label, value) for label, value in optional_fields if value)
    return rows


def render_avatar_placeholder(username: Optional[str]) -> None:
    avatar_text = build_avatar_text(username)
    st.markdown(
        f"""
        <div style="
            width: 88px;
            height: 88px;
            border-radius: 999px;
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            color: #1e3a8a;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 12px;
            border: 1px solid #93c5fd;
        ">{avatar_text}</div>
        """,
        unsafe_allow_html=True,
    )


def restore_return_context() -> None:
    context = st.session_state.get("public_profile_return_context", {})
    if isinstance(context, dict):
        for key, value in context.items():
            st.session_state[key] = value

    try:
        del st.query_params["user_id"]
    except Exception:
        pass
    st.session_state.pop("public_profile_target_user_id", None)


def go_back() -> None:
    return_page = st.session_state.get("public_profile_return_page", get_navigation_page("home"))
    restore_return_context()
    st.switch_page(return_page)


def main() -> None:
    require_auth()

    user_id = get_target_user_id()
    if user_id is None:
        st.error("Invalid profile link.")
        st.page_link(get_navigation_page("home"), label="🏠 Back to Home")
        return

    profile = load_public_profile(user_id)
    if profile is None:
        st.page_link(get_navigation_page("home"), label="🏠 Back to Home")
        return

    st.title(f"{profile.get('username', 'User')}'s Profile")
    st.caption("Only information the user chose to share is shown here.")

    return_page = st.session_state.get("public_profile_return_page")
    return_label = st.session_state.get("public_profile_return_label", "Back")
    if st.button(f"⬅️ {return_label}" if return_page else "🏠 Back to Home", key="public_profile_back"):
        go_back()

    render_avatar_placeholder(profile.get("username"))

    rows = build_public_profile_rows(profile)
    for label, value in rows:
        with st.container(border=True):
            st.markdown(f"**{label}**")
            st.write(value)

    if len(rows) == 1:
        st.info("This user has not shared any additional profile details yet.")


if __name__ == "__main__":
    main()
