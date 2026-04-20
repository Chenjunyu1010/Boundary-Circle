"""
Circle Hall Page - Browse and search circles

Displays all available circles with search/filter functionality.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Tuple

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
from views import circle_detail as circle_detail_page
from utils.auth import get_current_user, init_session_state, require_auth
from utils.api import api_client, response_json_object
from utils.ui import apply_button_usability_style

# Initialize session state
init_session_state()

# Page config
st.set_page_config(
    page_title="Circle Hall - Boundary Circle",
    page_icon="🏛",
)


def get_create_circle_button_columns() -> list[int]:
    """Return the column split used for the create-circle action row."""
    return [3, 7]


def build_category_filter_options(circles: list[dict]) -> list[str]:
    """Build dynamic category filter options from the fetched circles."""
    categories = sorted(
        {
            str(circle.get("category", "")).strip()
            for circle in circles
            if str(circle.get("category", "")).strip()
        }
    )
    return ["All", *categories]


def get_create_circle_category_options() -> list[str]:
    """Return available categories for new circles."""
    return [
        "General",
        "Course",
        "Interest",
        "Event",
        "Community",
        "Project",
        "Sports",
        "Entertainment",
    ]


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


def create_circle(
    name: str,
    description: str,
    category: str = "General",
) -> Tuple[bool, str, Optional[int]]:
    """Create a new circle."""
    current_user = get_current_user()
    if current_user.get("id") is None:
        return False, "Please login again before creating a circle.", None

    try:
        response = api_client.post(
            "/circles",
            data={
                "name": name,
                "description": description,
                "category": category,
            },
        )
        if response.ok:
            payload = response_json_object(response)
            return True, "Circle created successfully!", payload.get("id")
        return False, f"Failed to create circle: {response.reason}", None
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"Error: {exc}", None


def open_circle_detail(circle_id: int) -> None:
    """Persist selected circle id for inline detail view."""
    st.session_state.selected_circle_id = circle_id
    st.session_state.current_circle_id = circle_id


def prepare_circle_detail_navigation(circle_id: int) -> None:
    """Focus the newly created circle detail flow."""
    open_circle_detail(circle_id)
    st.session_state.circle_hall_focus_detail = True


def view_circle_detail(circle_id: int) -> None:
    """Open a circle detail view immediately on the current rerun."""
    prepare_circle_detail_navigation(circle_id)
    st.rerun()


def main() -> None:
    """Main page content for browsing circles and opening detail views."""
    apply_button_usability_style()

    st.title("Circle Hall")
    st.markdown("Discover and join circles that match your interests")

    # Require authentication
    require_auth()

    if (
        st.session_state.get("circle_hall_focus_detail")
        and st.session_state.get("selected_circle_id") is not None
    ):
        if st.button("⬅️ Back to Circle List", key="back_to_circle_list"):
            st.session_state.circle_hall_focus_detail = False
            st.rerun()
        circle_detail_page.main()
        return

    circles = fetch_circles()
    category_options = build_category_filter_options(circles)

    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input(
            "Search circles",
            placeholder="Enter circle name...",
        )

    with col2:
        category_filter = st.selectbox(
            "Category",
            category_options,
        )

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
    col1, col2 = st.columns(get_create_circle_button_columns())
    with col1:
        if st.button("➕ Create Circle", type="primary"):
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
                get_create_circle_category_options(),
            )

            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submit_btn = st.form_submit_button("✅ Create", type="primary")
            with col_cancel:
                cancel_btn = st.form_submit_button("❌ Cancel")

            if submit_btn:
                if not circle_name:
                    st.error("Please enter a circle name")
                else:
                    success, message, circle_id = create_circle(
                        circle_name,
                        circle_description,
                        circle_category,
                    )
                    if success:
                        st.session_state.show_create_form = False
                        st.session_state.circle_create_success_message = message
                        st.rerun()
                    else:
                        st.error(message)

            if cancel_btn:
                st.session_state.show_create_form = False
                st.rerun()

    st.markdown("---")
    success_message = st.session_state.pop("circle_create_success_message", None)
    if success_message:
        st.success(success_message)

    if not circles:
        st.info("No circles found. Be the first to create one!")
        return

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
                if circle.get("is_creator"):
                    st.caption("Status: You created this circle")
                elif circle.get("is_member"):
                    st.caption("Status: Joined")
                else:
                    st.caption("Status: Not joined")
                creator_label = circle.get("creator_username") or "Unknown"
                st.caption(f"Creator: {creator_label}")
                st.write(circle.get("description", "No description"))

                if st.button(
                    "Details",
                    key=f"view_circle_{circle.get('id')}",
                ):
                    view_circle_detail(circle.get("id"))

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
                    if circle.get("is_creator"):
                        st.caption("Status: You created this circle")
                    elif circle.get("is_member"):
                        st.caption("Status: Joined")
                    else:
                        st.caption("Status: Not joined")
                    creator_label = circle.get("creator_username") or "Unknown"
                    st.caption(f"Creator: {creator_label}")
                    st.write(
                        circle.get("description", "No description")
                    )

                    if st.button(
                        "Details",
                        key=f"view_circle_{circle.get('id')}",
                    ):
                        view_circle_detail(circle.get("id"))


if __name__ == "__main__":
    main()
