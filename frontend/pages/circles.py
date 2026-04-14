"""
Circle Hall Page - Browse and search circles

Displays all available circles with search/filter functionality.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
from views import circle_detail as circle_detail_page
from utils.auth import get_current_user, init_session_state, require_auth
from utils.api import api_client

# Initialize session state
init_session_state()

# Page config
st.set_page_config(
    page_title="Circle Hall - Boundary Circle",
    page_icon="🏛",
)


def fetch_circles() -> list[dict]:
    """Fetch all circles from API."""
    try:
        response = api_client.get("/circles")
        if response.ok:
            return response.json()
        st.error(f"Failed to load circles: {response.reason}")
        return []
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Error: {exc}")
        return []


def create_circle(name: str, description: str, category: str = "General") -> Tuple[bool, str]:
    """Create a new circle."""
    current_user = get_current_user()
    creator_id = current_user.get("id")
    if creator_id is None:
        return False, "Please login again before creating a circle."

    try:
        response = api_client.post(
            "/circles",
            data={
                "name": name,
                "description": description,
                "category": category,
            },
            params={"creator_id": creator_id},
        )
        if response.ok:
            return True, "Circle created successfully!"
        return False, f"Failed to create circle: {response.reason}"
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"Error: {exc}"


def open_circle_detail(circle_id: int) -> None:
    """Persist selected circle id for inline detail view."""
    st.session_state.selected_circle_id = circle_id
    st.session_state.current_circle_id = circle_id


def main() -> None:
    """Main page content with list and detail tabs."""
    st.title("Circle Hall")
    st.markdown("Discover and join circles that match your interests")

    # Require authentication
    require_auth()

    list_tab, detail_tab = st.tabs(["Circle List", "Circle Detail"])

    # --- List tab: search, create, and browse circles ---
    with list_tab:
        col1, col2 = st.columns([3, 1])

        with col1:
            search_query = st.text_input(
                "Search circles",
                placeholder="Enter circle name...",
            )

        with col2:
            category_filter = st.selectbox(
                "Category",
                ["All", "Course", "Interest", "Event", "Community", "General"],
            )

        circles = fetch_circles()

        if search_query:
            circles = [
                c
                for c in circles
                if search_query.lower() in c.get("name", "").lower()
                or search_query.lower() in c.get("description", "").lower()
            ]

        if category_filter != "All":
            circles = [c for c in circles if c.get("category") == category_filter]

        st.markdown("---")
        col1, col2 = st.columns([1, 9])
        with col1:
            if st.button("Create Circle", type="primary"):
                st.session_state.show_create_form = True

        if st.session_state.get("show_create_form", False):
            with st.form("create_circle_form"):
                st.markdown("### Create New Circle")
                circle_name = st.text_input(
                    "Circle Name",
                    placeholder="Enter circle name",
                )
                circle_description = st.text_area(
                    "Description",
                    placeholder="Describe your circle",
                )
                circle_category = st.selectbox(
                    "Category",
                    ["General", "Course", "Interest", "Event", "Community"],
                )

                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submit_btn = st.form_submit_button("Create", type="primary")
                with col_cancel:
                    cancel_btn = st.form_submit_button("Cancel")

                if submit_btn:
                    if not circle_name:
                        st.error("Please enter a circle name")
                    else:
                        success, message = create_circle(
                            circle_name,
                            circle_description,
                            circle_category,
                        )
                        if success:
                            st.success(message)
                            st.session_state.show_create_form = False
                            st.rerun()
                        else:
                            st.error(message)

                if cancel_btn:
                    st.session_state.show_create_form = False
                    st.rerun()

        st.markdown("---")
        if not circles:
            st.info("No circles found. Be the first to create one!")
        else:
            st.markdown(f"### Available Circles ({len(circles)})")

            for i in range(0, len(circles), 2):
                col1, col2 = st.columns(2)

                with col1:
                    circle = circles[i]
                    with st.container(border=True):
                        st.markdown(f"**{circle.get('name', 'Unnamed')}**")
                        st.caption(
                            f"Category: {circle.get('category', 'General')}"
                        )
                        st.write(circle.get("description", "No description"))

                        if st.button(
                            "View Details ->",
                            key=f"view_circle_{circle.get('id')}",
                        ):
                            open_circle_detail(circle.get("id"))

                if i + 1 < len(circles):
                    with col2:
                        circle = circles[i + 1]
                        with st.container(border=True):
                            st.markdown(
                                f"**{circle.get('name', 'Unnamed')}**"
                            )
                            st.caption(
                                f"Category: {circle.get('category', 'General')}"
                            )
                            st.write(
                                circle.get("description", "No description")
                            )

                            if st.button(
                                "View Details ->",
                                key=f"view_circle_{circle.get('id')}",
                            ):
                                open_circle_detail(circle.get("id"))

    # --- Detail tab: reuse full circle_detail layout inside the tab ---
    with detail_tab:
        circle_id = st.session_state.get("selected_circle_id")
        if circle_id is None:
            st.info(
                "Select a circle from the list tab to view its details.",
            )
            return

        # Ensure circle_detail resolves the same id
        st.session_state.current_circle_id = circle_id

        # Delegate rendering to the original circle_detail main function
        circle_detail_page.main()


if __name__ == "__main__":
    main()
