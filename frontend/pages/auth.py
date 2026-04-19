"""
Login and Registration Page

Provides user authentication with login and registration forms.
"""

import streamlit as st

# Add parent directory to path for imports
import sys
from pathlib import Path

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.auth import login, register, is_authenticated, init_session_state
from utils.ui import apply_button_usability_style
from utils.validation import validate_email, validate_password, validate_username

# Initialize session state
init_session_state()

# Page config
st.set_page_config(
    page_title="Login - Boundary Circle",
    page_icon="🔐"
)

def handle_login(email: str, password: str):
    """Handle login form submission."""
    valid, msg = validate_email(email)
    if not valid:
        st.error(msg)
        return

    if not password:
        st.error("Please enter your password")
        return

    with st.spinner("Logging in..."):
        success, message = login(email, password)

    if success:
        st.balloons()
        st.success(message)
        st.switch_page("Home.py")
    else:
        st.error(message)


def handle_register(username: str, email: str, password: str, confirm_password: str):
    """Handle registration form submission."""
    valid, msg = validate_username(username)
    if not valid:
        st.error(msg)
        return

    valid, msg = validate_email(email)
    if not valid:
        st.error(msg)
        return

    valid, msg = validate_password(password)
    if not valid:
        st.error(msg)
        return

    if password != confirm_password:
        st.error("Passwords do not match")
        return

    with st.spinner("Registering..."):
        success, message = register(username, email, password)

    if success:
        st.success(message)
        st.toast("Registration successful, please login")
    else:
        st.error(message)


def main():
    """Main page content."""
    apply_button_usability_style()

    st.title("Login / Register")
    st.markdown("Welcome to Boundary Circle")

    if is_authenticated():
        from utils.auth import get_current_user
        user = get_current_user()
        st.info(f"You are logged in as: {user.get('username', 'User')}")
        st.page_link("Home.py", label="Go to Home", icon="🏠")
        return

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")

            submit_login = st.form_submit_button("🔑 Login", type="primary")

            if submit_login:
                handle_login(email, password)

        st.markdown("---")
        st.caption("Tip: In Mock mode, you can use any email and password")

    with tab_register:
        with st.form("register_form"):
            username = st.text_input("Username", placeholder="your_username")
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")

            st.caption("Password must be at least 6 characters")

            submit_register = st.form_submit_button("📝 Register", type="primary")

            if submit_register:
                handle_register(username, email, password, confirm_password)


if __name__ == "__main__":
    main()
