"""
Circle Detail Page - View circle details and join/leave circles

Displays circle information, members, and allows joining/leaving.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
from utils.auth import get_current_user, init_session_state, require_auth
from utils.api import api_client

# Initialize session state
init_session_state()

# Page config
st.set_page_config(
    page_title="Circle Detail - Boundary Circle",
    page_icon="📋"
)


def fetch_circle_detail(circle_id: int):
    """Fetch circle details from API."""
    try:
        response = api_client.get(f"/circles/{circle_id}")
        if response.ok:
            return response.json()
        else:
            st.error(f"Failed to load circle: {response.reason}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def fetch_circle_members(circle_id: int):
    """Fetch circle members from API."""
    try:
        response = api_client.get(f"/circles/{circle_id}/members")
        if response.ok:
            return response.json()
        else:
            return []
    except Exception:
        return []


def fetch_circle_tags(circle_id: int):
    """Fetch circle tag definitions from API."""
    try:
        response = api_client.get(f"/circles/{circle_id}/tags")
        if response.ok:
            return response.json()
        else:
            return []
    except Exception:
        return []


def normalize_tag_definition(tag: dict) -> dict:
    """Normalize mock and backend tag definitions to a single format."""
    tag_data_type = tag.get("data_type")
    legacy_type = tag.get("type")
    normalized_type = tag_data_type or legacy_type or "string"
    options = tag.get("options")

    if isinstance(options, str):
        try:
            options = json.loads(options)
        except json.JSONDecodeError:
            options = None

    return {
        "id": tag.get("id"),
        "name": tag.get("name", ""),
        "data_type": normalized_type,
        "required": tag.get("required", False),
        "options": options,
    }


def resolve_circle_id(query_params=None) -> int:
    """Resolve current circle id from session state or query params."""
    selected_circle_id = st.session_state.get("selected_circle_id")
    if selected_circle_id is not None:
        try:
            return int(selected_circle_id)
        except (TypeError, ValueError):
            pass

    params = query_params if query_params is not None else st.query_params
    circle_id = params.get("circle_id", 1)
    try:
        return int(circle_id)
    except (ValueError, TypeError):
        return 1


def join_circle(circle_id: int, tag_definitions: list, tag_data: dict) -> tuple[bool, str]:
    """Join a circle with tag data."""
    current_user = get_current_user()
    current_user_id = current_user.get("id")
    if current_user_id is None:
        return False, "Please login again before joining a circle."

    try:
        if api_client.mock_mode:
            response = api_client.post(f"/circles/{circle_id}/join", data=tag_data)
            if response.ok:
                return True, "Successfully joined the circle!"
            return False, f"Failed to join: {response.reason}"

        normalized_tags = [normalize_tag_definition(tag) for tag in tag_definitions]
        for tag in normalized_tags:
            value = tag_data.get(tag["name"])
            if value in (None, "", []):
                continue

            if isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            else:
                value = str(value)

            response = api_client.post(
                f"/circles/{circle_id}/tags/submit",
                data={
                    "tag_definition_id": tag["id"],
                    "value": value,
                },
                params={"current_user_id": current_user_id},
            )
            if not response.ok:
                return False, f"Failed to submit tags: {response.reason}"

        st.session_state.setdefault("joined_circles", [])
        if circle_id not in st.session_state.joined_circles:
            st.session_state.joined_circles.append(circle_id)
        return True, "Successfully joined the circle!"
    except Exception as e:
        return False, f"Error: {str(e)}"


def leave_circle(circle_id: int) -> tuple[bool, str]:
    """Leave a circle."""
    current_user = get_current_user()
    current_user_id = current_user.get("id")
    if current_user_id is None:
        return False, "Please login again before leaving a circle."

    try:
        if api_client.mock_mode:
            response = api_client.delete(f"/circles/{circle_id}/leave")
            if response.ok:
                return True, "Successfully left the circle"
            return False, f"Failed to leave: {response.reason}"

        my_tags_response = api_client.get(
            f"/circles/{circle_id}/tags/my",
            params={"current_user_id": current_user_id},
        )
        if not my_tags_response.ok:
            return False, f"Failed to leave: {my_tags_response.reason}"

        for user_tag in my_tags_response.json():
            delete_response = api_client.delete(
                f"/tags/{user_tag['id']}",
                params={"current_user_id": current_user_id},
            )
            if not delete_response.ok:
                return False, f"Failed to leave: {delete_response.reason}"

        joined_circles = st.session_state.get("joined_circles", [])
        if circle_id in joined_circles:
            joined_circles.remove(circle_id)
        return True, "Successfully left the circle"
    except Exception as e:
        return False, f"Error: {str(e)}"


def is_circle_joined(circle_id: int) -> bool:
    """Check if user has joined the circle."""
    joined_circles = st.session_state.get("joined_circles", [])
    return circle_id in joined_circles


def render_tag_form(tag_definitions: list, circle_id: int):
    """Render dynamic tag form based on tag definitions."""
    if not tag_definitions:
        st.info("This circle has no required tags")
        return {}

    tag_data = {}

    with st.form(f"tag_form_{circle_id}"):
        st.markdown("### 📝 Fill in Your Information")

        normalized_tags = [normalize_tag_definition(tag) for tag in tag_definitions]

        for tag in normalized_tags:
            tag_name = tag["name"]
            tag_type = tag["data_type"]
            tag_required = tag["required"]
            tag_options = tag["options"]

            # Required tag marker
            label = f"{tag_name} *" if tag_required else tag_name

            if tag_type in ("text", "string"):
                tag_data[tag_name] = st.text_input(label, key=f"tag_{circle_id}_{tag.get('id')}")
            elif tag_type in ("select", "enum") and tag_options:
                tag_data[tag_name] = st.selectbox(label, tag_options, key=f"tag_{circle_id}_{tag.get('id')}")
            elif tag_type == "multiselect" and tag_options:
                tag_data[tag_name] = st.multiselect(label, tag_options, key=f"tag_{circle_id}_{tag.get('id')}")
            elif tag_type in ("number", "integer"):
                tag_data[tag_name] = st.number_input(label, step=1, format="%d", key=f"tag_{circle_id}_{tag.get('id')}")
            elif tag_type == "float":
                tag_data[tag_name] = st.number_input(label, key=f"tag_{circle_id}_{tag.get('id')}")
            elif tag_type == "boolean":
                tag_data[tag_name] = st.checkbox(label, key=f"tag_{circle_id}_{tag.get('id')}")
            elif tag_type == "textarea":
                tag_data[tag_name] = st.text_area(label, key=f"tag_{circle_id}_{tag.get('id')}")
            else:
                tag_data[tag_name] = st.text_input(label, key=f"tag_{circle_id}_{tag.get('id')}")

        # Validation for required tags
        submitted = st.form_submit_button("Submit", type="primary")

        if submitted:
            # Check required fields
            missing_fields = []
            for tag in normalized_tags:
                value = tag_data.get(tag["name"])
                if tag["required"] and value in (None, "", []):
                    missing_fields.append(tag["name"])

            if missing_fields:
                st.error(f"Please fill in required fields: {', '.join(missing_fields)}")
                return None

            return tag_data

    return None


def main():
    """Main page content."""
    circle_id = resolve_circle_id()

    # Require authentication
    require_auth()

    # Fetch circle data
    circle = fetch_circle_detail(circle_id)

    if not circle:
        st.error("Circle not found")
        st.page_link("2_Circles.py", label="<- Back to Circle Hall", icon="🏠")
        return

    # Check join status
    joined = is_circle_joined(circle_id)

    # Page header
    st.title(f"📋 {circle.get('name', 'Circle')}")
    st.markdown(f"**Category:** {circle.get('category', 'General')}")
    st.markdown(f"**Description:** {circle.get('description', 'No description')}")

    # Back link
    st.page_link("2_Circles.py", label="<- Back to Circle Hall", icon="🏠")

    st.markdown("---")

    # Join/Leave section
    col1, col2 = st.columns([1, 2])

    with col1:
        if joined:
            st.success("✓ You are a member")
            if st.button("🚪 Leave Circle", type="secondary"):
                success, message = leave_circle(circle_id)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        else:
            st.warning("You haven't joined this circle yet")
            if st.button("➕ Join Circle", type="primary"):
                st.session_state.show_join_form = True

    # Show join form if requested
    if not joined and st.session_state.get("show_join_form", False):
        with col2:
            tag_definitions = fetch_circle_tags(circle_id)

            tag_data = render_tag_form(tag_definitions, circle_id)

            if tag_data is not None:
                # Submit join request
                success, message = join_circle(circle_id, tag_definitions, tag_data)
                if success:
                    st.success(message)
                    st.session_state.show_join_form = False
                    st.rerun()
                else:
                    st.error(message)

            # Cancel button
            if st.button("Cancel", key="cancel_join"):
                st.session_state.show_join_form = False
                st.rerun()

    st.markdown("---")

    # Members section
    st.markdown("### 👥 Members")

    members = fetch_circle_members(circle_id)

    if members:
        for member in members:
            with st.container(border=True):
                col1, col2 = st.columns([1, 4])
                with col1:
                    # Use st.image with a placeholder avatar or initials
                    initial = member.get("username", "U")[0].upper()
                    st.markdown(f"<div style='font-size:24px;text-align:center;'>👤</div>", unsafe_allow_html=True)
                    st.caption(f"**{initial}**")
                with col2:
                    st.markdown(f"**{member.get('username', 'Unknown')}**")
                    st.caption(member.get("email", ""))
    else:
        st.info("No members yet. Be the first to join!")

    # Tags section (informational)
    st.markdown("---")
    st.markdown("### 🏷️ Circle Tags")

    tag_definitions = fetch_circle_tags(circle_id)

    if tag_definitions:
        for tag in [normalize_tag_definition(tag) for tag in tag_definitions]:
            with st.container(border=True):
                col1, col2 = st.columns([1, 4])
                with col1:
                    required = "🔴" if tag.get("required") else "⚪"
                    st.markdown(f"**{tag.get('name', 'Tag')}** {required}")
                with col2:
                    st.markdown(f"Type: {tag.get('data_type', 'string')}")
                    if tag.get("options"):
                        st.caption(f"Options: {', '.join(tag.get('options', []))}")
    else:
        st.info("No tags defined for this circle")


if __name__ == "__main__":
    main()
