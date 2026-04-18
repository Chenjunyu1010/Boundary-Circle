"""
Home Page - Main navigation page for Boundary Circle
"""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.auth import get_current_user, init_session_state, is_authenticated, logout
from utils.api import api_client


init_session_state()

st.set_page_config(
    page_title="Boundary Circle",
    page_icon="BC",
)


def load_profile_summary() -> dict:
    response = api_client.get("/profile/me")
    if not response.ok:
        return {}
    return response.json()


def build_account_summary(user: dict, profile: dict) -> list[tuple[str, str, str | None]]:
    rows: list[tuple[str, str, str | None]] = [
        ("Username", user.get("username", "User"), None),
    ]

    visibility_map = {
        "full_name": "show_full_name",
        "email": "show_email",
        "gender": "show_gender",
        "birthday": "show_birthday",
        "bio": "show_bio",
    }
    values = {
        "full_name": user.get("full_name") or "Not set",
        "email": user.get("email", "N/A"),
        "gender": profile.get("gender") or "Not set",
        "birthday": profile.get("birthday") or "Not set",
        "bio": profile.get("bio") or "Not set",
    }
    labels = {
        "full_name": "Full name",
        "email": "Email",
        "gender": "Gender",
        "birthday": "Birthday",
        "bio": "Bio",
    }

    for key in ["full_name", "email", "gender", "birthday", "bio"]:
        visibility = None if profile.get(visibility_map[key], True) else "Hidden"
        rows.append((labels[key], values[key], visibility))

    return rows


def format_account_summary_row(label: str, value: str, visibility: str | None) -> str:
    if visibility is None:
        return f"<strong>{label}:</strong> {value}"

    badge_color = "#6b7280" if visibility == "Hidden" else "#9ca3af"
    return (
        f"<strong>{label}:</strong> {value} "
        f"<span style='color:{badge_color}; font-size:0.85em;'>({visibility})</span>"
    )


def main():
    """Main page content."""
    st.title("Boundary Circle")
    st.markdown("Your social circle management platform")

    if is_authenticated():
        user = get_current_user()
        username = user.get("username", "User")
        profile = load_profile_summary()

        st.success(f"Welcome back, {username}!")

        if st.session_state.get("show_profile_completion_prompt"):
            st.info("This looks like your first login. Complete your personal profile now, or skip it and return later.")
            prompt_col1, prompt_col2 = st.columns(2)
            with prompt_col1:
                st.page_link("pages/profile.py", label="Complete Profile")
            with prompt_col2:
                if st.button("Skip for now"):
                    response = api_client.post("/profile/me/dismiss-prompt")
                    if response.ok:
                        st.session_state.show_profile_completion_prompt = False
                        st.rerun()

        st.markdown("### Navigation")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.page_link("pages/auth.py", label="Login/Register")
            st.page_link("pages/circles.py", label="Circle Hall")

        with col2:
            st.page_link("pages/profile.py", label="My Profile")

        with col3:
            if st.button("Logout"):
                logout()
                st.rerun()

        st.markdown("---")
        st.markdown("### Account Summary")
        for label, value, visibility in build_account_summary(user, profile):
            st.markdown(format_account_summary_row(label, value, visibility), unsafe_allow_html=True)
        st.write("Use the dedicated profile page to manage personal details and visibility.")

    else:
        st.warning("Please login to access all features")
        st.page_link("pages/auth.py", label="Login / Register")
        st.markdown("---")
        st.info("This is the home page. Use the link above to login or register an account.")


if __name__ == "__main__":
    main()
