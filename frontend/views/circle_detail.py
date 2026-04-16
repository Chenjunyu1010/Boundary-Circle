"""
Circle Detail Page - View circle details and join/leave circles

Displays circle information, members, and allows joining/leaving.
"""

import json
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
from utils.auth import get_current_user, init_session_state, require_auth
from utils.api import api_client

# Initialize session state
init_session_state()


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


def create_tag_definition(
    circle_id: int,
    name: str,
    data_type: str,
    required: bool,
    options: Optional[str],
    max_selections: Optional[int] = None,
) -> tuple[bool, str]:
    """Create a tag definition for a circle (creator only)."""
    current_user = get_current_user()
    user_id = current_user.get("id") if current_user else None
    if user_id is None:
        return False, "Please login again before creating tag definitions."

    try:
        response = api_client.post(
            f"/circles/{circle_id}/tags",
            data={
                "name": name,
                "data_type": data_type,
                "required": required,
                "options": options,
                "max_selections": max_selections,
                "description": None,
            },
        )
        if response.ok:
            return True, "Tag definition created successfully."

        detail = ""
        try:
            detail = response.json().get("detail", "")
        except Exception:
            detail = ""
        return False, detail or f"Failed to create tag definition: {response.reason}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def submit_member_tags(circle_id: int, tag_definitions: list, tag_data: dict) -> tuple[bool, str]:
    """Submit or update current member tags for a circle."""
    current_user = get_current_user()
    user_id = current_user.get("id") if current_user else None
    if user_id is None:
        return False, "Please login again before updating your tags."

    try:
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
                data={"tag_definition_id": tag["id"], "value": value},
            )
            if not response.ok:
                detail = ""
                try:
                    detail = response.json().get("detail", "")
                except Exception:
                    detail = ""
                return False, detail or f"Failed to submit tag values: {response.reason}"

        return True, "Your tags have been updated."
    except Exception as e:
        return False, f"Error: {str(e)}"


def normalize_tag_definition(tag: dict) -> dict:
    """Normalize mock and backend tag definitions to a single format."""
    tag_data_type = tag.get("data_type")
    legacy_type = tag.get("type")
    normalized_type = tag_data_type or legacy_type or "string"
    type_aliases = {
        "text": "string",
        "select": "single_select",
        "multiselect": "multi_select",
        "number": "integer",
    }
    normalized_type = type_aliases.get(normalized_type, normalized_type)
    options = tag.get("options")

    if isinstance(options, str):
        try:
            options = json.loads(options)
        except json.JSONDecodeError:
            options = None

    normalized_tag = {
        "id": tag.get("id"),
        "name": tag.get("name", ""),
        "data_type": normalized_type,
        "required": tag.get("required", False),
        "options": options,
    }
    if "max_selections" in tag and tag.get("max_selections") is not None:
        normalized_tag["max_selections"] = tag.get("max_selections")
    return normalized_tag


def validate_tag_input(tag: dict, value) -> tuple[bool, str]:
    """Validate a frontend tag input before sending it to the backend."""
    if value in (None, "", []):
        return True, ""

    if tag.get("data_type") == "multi_select":
        max_selections = tag.get("max_selections")
        if max_selections is not None and len(value) > max_selections:
            return False, f"{tag['name']} allows at most {max_selections} selections."

    return True, ""


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
    if not current_user:
        return False, "Please login again before joining a circle."
    user_id = current_user.get("id")
    if user_id is None:
        return False, "Please login again before joining a circle."

    try:
        join_resp = api_client.post(f"/circles/{circle_id}/join")
        if not join_resp.ok:
            detail = ""
            try:
                detail = join_resp.json().get("detail", "")
            except Exception:
                detail = ""
            return False, detail or f"Failed to join circle: {join_resp.reason}"

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
            )
            if not response.ok:
                detail = ""
                try:
                    detail = response.json().get("detail", "")
                except Exception:
                    detail = ""
                return False, detail or f"Failed to submit tags: {response.reason}"
        return True, "Successfully joined the circle!"
    except Exception as e:
        return False, f"Error: {str(e)}"


def leave_circle(circle_id: int) -> tuple[bool, str]:
    """Leave a circle."""
    if not get_current_user():
        return False, "Please login again before leaving a circle."

    try:
        leave_resp = api_client.delete(f"/circles/{circle_id}/leave")
        if not leave_resp.ok:
            return False, f"Failed to leave: {leave_resp.reason}"

        return True, "Successfully left the circle"
    except Exception as e:
        return False, f"Error: {str(e)}"


def is_circle_joined(circle_id: int) -> bool:
    """Check if user has joined the circle via real Backend API."""
    current_user = get_current_user()
    if not current_user:
        return False
    user_id = current_user.get("id")
    members = fetch_circle_members(circle_id)
    return any((m.get("id") or m.get("user_id")) == user_id for m in members)


def render_tag_form(tag_definitions: list, circle_id: int):
    """Render dynamic tag form based on tag definitions."""
    if not tag_definitions:
        st.info("This circle has no required tags")
        # No form submission when there are no tags; signal this with None
        return None

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
            elif tag_type in ("single_select", "enum") and tag_options:
                tag_data[tag_name] = st.selectbox(label, tag_options, key=f"tag_{circle_id}_{tag.get('id')}")
            elif tag_type == "multi_select" and tag_options:
                help_text = None
                if tag.get("max_selections") is not None:
                    help_text = f"Select up to {tag['max_selections']} options."
                tag_data[tag_name] = st.multiselect(
                    label,
                    tag_options,
                    key=f"tag_{circle_id}_{tag.get('id')}",
                    help=help_text,
                )
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

            validation_errors = []
            for tag in normalized_tags:
                is_valid, error_message = validate_tag_input(tag, tag_data.get(tag["name"]))
                if not is_valid:
                    validation_errors.append(error_message)

            if validation_errors:
                st.error(" ".join(validation_errors))
                return None

            return tag_data

    return None


def main():
    """Main page content."""
    circle_id = resolve_circle_id()
    st.session_state.current_circle_id = circle_id

    # Require authentication
    require_auth()

    # Fetch circle data
    circle = fetch_circle_detail(circle_id)

    if not circle:
        st.error("Circle not found")
        st.page_link("pages/circles.py", label="Back to Circle Hall", icon="⬅️")
        return

    # Check join status
    joined = is_circle_joined(circle_id)

    # Page header
    st.title(f"🔵 {circle.get('name', 'Circle')}")
    st.markdown(f"**Category:** {circle.get('category', 'General')}")
    st.markdown(f"**Description:** {circle.get('description', 'No description')}")

    # Back link
    st.page_link("pages/circles.py", label="Back to Circle Hall", icon="⬅️")

    st.markdown("---")

    current_user = get_current_user()
    current_user_id = current_user.get("id") if current_user else None
    is_creator = current_user_id is not None and current_user_id == circle.get("creator_id")

    # Join/Leave section
    col1, col2 = st.columns([1, 2])

    with col1:
        if joined:
            st.success("✅ You are a member")
            st.page_link("pages/team_management.py", label="Go to Team Management", icon="👥")
            if st.button("🚪 Leave Circle", type="secondary"):
                success, message = leave_circle(circle_id)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        else:
            st.warning("You haven't joined this circle yet")
            if st.button("? Join Circle", type="primary"):
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

    # Member self-service tag updates
    if joined:
        with col2:
            with st.expander("🔄 Update My Tags", expanded=False):
                tag_definitions_for_update = fetch_circle_tags(circle_id)
                if not tag_definitions_for_update:
                    st.info("No tag definitions available for this circle yet.")
                else:
                    with st.form(f"update_my_tags_form_{circle_id}"):
                        st.caption("Update your own tag values for this circle")
                        normalized_tags = [normalize_tag_definition(tag) for tag in tag_definitions_for_update]
                        tag_data: dict[str, object] = {}

                        for tag in normalized_tags:
                            tag_name = tag["name"]
                            tag_type = tag["data_type"]
                            tag_required = tag["required"]
                            tag_options = tag["options"]
                            label = f"{tag_name} *" if tag_required else tag_name

                            if tag_type in ("string", "text"):
                                tag_data[tag_name] = st.text_input(label, key=f"update_tag_{circle_id}_{tag.get('id')}")
                            elif tag_type == "integer":
                                tag_data[tag_name] = st.number_input(
                                    label,
                                    step=1,
                                    format="%d",
                                    key=f"update_tag_{circle_id}_{tag.get('id')}",
                                )
                            elif tag_type == "float":
                                tag_data[tag_name] = st.number_input(label, key=f"update_tag_{circle_id}_{tag.get('id')}")
                            elif tag_type == "boolean":
                                tag_data[tag_name] = st.checkbox(label, key=f"update_tag_{circle_id}_{tag.get('id')}")
                            elif tag_type in ("single_select", "enum") and tag_options:
                                tag_data[tag_name] = st.selectbox(
                                    label,
                                    tag_options,
                                    key=f"update_tag_{circle_id}_{tag.get('id')}",
                                )
                            elif tag_type == "multi_select" and tag_options:
                                help_text = None
                                if tag.get("max_selections") is not None:
                                    help_text = f"Select up to {tag['max_selections']} options."
                                tag_data[tag_name] = st.multiselect(
                                    label,
                                    tag_options,
                                    key=f"update_tag_{circle_id}_{tag.get('id')}",
                                    help=help_text,
                                )
                            else:
                                tag_data[tag_name] = st.text_input(label, key=f"update_tag_{circle_id}_{tag.get('id')}")

                        save_my_tags = st.form_submit_button("Save My Tags", type="primary")

                        if save_my_tags:
                            missing_fields = []
                            for tag in normalized_tags:
                                value = tag_data.get(tag["name"])
                                if tag["required"] and value in (None, "", []):
                                    missing_fields.append(tag["name"])
                            if missing_fields:
                                st.error(f"Please fill in required fields: {', '.join(missing_fields)}")
                            else:
                                validation_errors = []
                                for tag in normalized_tags:
                                    is_valid, error_message = validate_tag_input(tag, tag_data.get(tag["name"]))
                                    if not is_valid:
                                        validation_errors.append(error_message)
                                if validation_errors:
                                    st.error(" ".join(validation_errors))
                                    return
                                success, message = submit_member_tags(circle_id, tag_definitions_for_update, tag_data)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)

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
                    required = "⭐" if tag.get("required") else "?"
                    st.markdown(f"**{tag.get('name', 'Tag')}** {required}")
                with col2:
                    st.markdown(f"Type: {tag.get('data_type', 'string')}")
                    if tag.get("options"):
                        st.caption(f"Options: {', '.join(tag.get('options', []))}")
    else:
        st.info("No tags defined for this circle")

    if is_creator:
        st.markdown("---")
        st.markdown("### 🔐 Admin Tag Management")
        with st.form(f"add_tag_definition_form_{circle_id}"):
            st.markdown("#### ➕ Add New Tag Definition")
            new_tag_name = st.text_input("name", placeholder="e.g. Major")
            new_tag_type = st.selectbox(
                "data_type",
                ["string", "integer", "float", "boolean", "single_select", "multi_select"],
            )
            new_tag_required = st.checkbox("required", value=False)
            new_tag_options = st.text_input(
                "options",
                placeholder='When type is selection-based, input JSON array like ["A", "B"]',
            )
            new_tag_max_selections = st.number_input("max_selections", min_value=1, step=1, value=1)

            create_tag_submit = st.form_submit_button("Create Tag Definition", type="primary")

            if create_tag_submit:
                if not new_tag_name.strip():
                    st.error("name is required")
                else:
                    options_payload: Optional[str] = None
                    max_selections_payload: Optional[int] = None
                    if new_tag_type in {"single_select", "multi_select"}:
                        if not new_tag_options.strip():
                            st.error("options is required for selection types")
                            options_payload = None
                        else:
                            try:
                                parsed_options = json.loads(new_tag_options)
                                if not isinstance(parsed_options, list) or not parsed_options:
                                    raise ValueError
                                options_payload = json.dumps(parsed_options, ensure_ascii=False)
                            except Exception:
                                st.error("options must be a valid non-empty JSON array, e.g. [\"A\", \"B\"]")
                                options_payload = None
                        if new_tag_type == "multi_select" and options_payload is not None:
                            max_selections_payload = int(new_tag_max_selections)
                    elif new_tag_options.strip():
                        options_payload = new_tag_options.strip()

                    if new_tag_type not in {"single_select", "multi_select"} or options_payload is not None:
                        success, message = create_tag_definition(
                            circle_id,
                            new_tag_name.strip(),
                            new_tag_type,
                            new_tag_required,
                            options_payload,
                            max_selections_payload,
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)


if __name__ == "__main__":
    main()
