"""
Home Page - Main navigation page for Boundary Circle
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st

from utils.auth import (
    init_session_state,
    is_authenticated,
    get_current_user,
    logout
)

# Initialize session state
init_session_state()

# Page config
st.set_page_config(
    page_title="Boundary Circle",
    page_icon="⭕"
)


def main():
    """Main page content."""
    st.title("Boundary Circle")
    st.markdown("Your social circle management platform")

    if is_authenticated():
        # Logged in state
        user = get_current_user()
        username = user.get("username", "User")

        st.success(f"Welcome back, {username}!")

        # Navigation
        st.markdown("### Navigation")
        col1, col2 = st.columns(2)

        with col1:
            st.page_link("pages/1_auth.py", label="Login/Register", icon="🔐")

        with col2:
            if st.button("Logout", icon="🚪"):
                logout()
                st.rerun()

        # User info
        st.markdown("---")
        st.markdown("### Your Profile")
        st.write(f"**Username:** {username}")
        st.write(f"**Email:** {user.get('email', 'N/A')}")

    else:
        # Not logged in state
        st.warning("Please login to access all features")

        col1, col2 = st.columns(2)

        with col1:
            st.page_link("pages/1_auth.py", label="Login / Register", icon="🔐")

        st.markdown("---")
        st.info("This is the home page. Use the link above to login or register an account.")


if __name__ == "__main__":
    main()
