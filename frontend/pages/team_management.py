"""    
Team management page.

Provides team listing, creation, invitation sending, invitation handling,
plus matching-based recommendations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable, Optional, Tuple

import streamlit as st


parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.api import api_client
from utils.auth import get_current_user, init_session_state, require_auth
from utils.ui import apply_button_usability_style, render_button_variant_marker


init_session_state()

TEAM_REQUIREMENT_MODE_NOT_REQUIRED = "not_required"
TEAM_REQUIREMENT_MODE_REQUIRED_ONLY = "required_only"
TEAM_REQUIREMENT_MODE_MATCH_VALUE = "match_value"
TEAM_REQUIREMENT_MODE_OPTIONS = [
    TEAM_REQUIREMENT_MODE_NOT_REQUIRED,
    TEAM_REQUIREMENT_MODE_REQUIRED_ONLY,
    TEAM_REQUIREMENT_MODE_MATCH_VALUE,
]

st.set_page_config(
    page_title="Team Management - Boundary Circle",
    page_icon="\U0001F465",
)


def fetch_teams(circle_id: int) -> list[dict]:
    """Fetch teams for a circle."""
    try:
        response = api_client.get(f"/circles/{circle_id}/teams")
        if response.ok:
            return response.json()
        if response.status_code == 403:
            st.warning("Join this circle before viewing its teams.")
            return []
        st.error(f"Failed to load teams: {response.reason}")
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Error loading teams: {exc}")
    return []


def fetch_circle_members(circle_id: int) -> list[dict]:
    """Fetch circle members."""
    try:
        response = api_client.get(f"/circles/{circle_id}/members")
        if response.ok:
            return response.json()
        if response.status_code == 403:
            st.warning("Join this circle before viewing its members.")
            return []
        st.error(f"Failed to load members: {response.reason}")
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Error loading members: {exc}")
    return []


def can_access_current_circle(circle_id: int) -> bool:
    """Return whether the current user can access team features for this circle."""
    try:
        response = api_client.get(f"/circles/{circle_id}/members")
        if response.ok:
            return True
        if response.status_code == 403:
            st.warning("You must join this circle before accessing team management.")
            return False
        st.error(f"Failed to verify circle access: {response.reason}")
        return False
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Error verifying circle access: {exc}")
        return False


def open_team_detail(team_id: int) -> None:
    """Persist selected team id and switch to detail mode."""
    st.session_state.selected_team_id = team_id
    st.session_state.team_management_focus_detail = True
    st.rerun()


def close_team_detail() -> None:
    """Return from the team detail view to the tabbed overview."""
    st.session_state.team_management_focus_detail = False
    st.rerun()


def go_to_circle_detail() -> None:
    """Return to the current circle detail page."""
    circle_id = st.session_state.get("current_circle_id")
    if circle_id is not None:
        st.session_state.selected_circle_id = circle_id
    st.session_state.circle_hall_focus_detail = True
    st.switch_page("pages/circles.py")


def go_to_circle_hall() -> None:
    """Return to the circle hall list view."""
    st.session_state.circle_hall_focus_detail = False
    st.session_state.pop("selected_circle_id", None)
    st.switch_page("pages/circles.py")


def open_public_profile(user_id: int) -> None:
    """Open the public profile page for a team-related user."""
    st.session_state.public_profile_return_page = "pages/team_management.py"
    st.session_state.public_profile_return_label = "Back to Team Management"
    st.session_state.public_profile_target_user_id = int(user_id)
    st.session_state.public_profile_return_context = {
        "current_circle_id": st.session_state.get("current_circle_id"),
        "selected_team_id": st.session_state.get("selected_team_id"),
        "team_management_focus_detail": st.session_state.get("team_management_focus_detail", False),
    }
    st.query_params["user_id"] = str(user_id)
    st.switch_page("pages/public_profile.py")


def get_selected_team(teams: list[dict]) -> Optional[dict]:
    """Return the currently selected team from a fetched team list."""
    selected_team_id = st.session_state.get("selected_team_id")
    if selected_team_id is None:
        return None
    return next((team for team in teams if team.get("id") == selected_team_id), None)


def fetch_circle_tags(circle_id: int) -> list[dict]:
    """Fetch tag definitions for the current circle."""
    try:
        response = api_client.get(f"/circles/{circle_id}/tags")
        if response.ok:
            return response.json()
        st.error(f"Failed to load circle tags: {response.reason}")
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Error loading circle tags: {exc}")
    return []


def fetch_invitations() -> list[dict]:
    """Fetch invitations related to the current user."""
    try:
        response = api_client.get("/invitations")
        if response.ok:
            return response.json()
        st.error(f"Failed to load invitations: {response.reason}")
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Error loading invitations: {exc}")
    return []


def fetch_team_invitations(team_id: int) -> list[dict]:
    """Fetch invitations associated with a specific team."""
    try:
        response = api_client.get(f"/teams/{team_id}/invitations")
        if response.ok:
            return response.json()
        st.error(f"Failed to load team invitations: {response.reason}")
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Error loading team invitations: {exc}")
    return []


def fetch_matching_users(team_id: int) -> list[dict]:
    """Fetch matching user recommendations for a given team.

    Returns a list of UserMatch-like dicts from `/matching/users`.
    """
    try:
        response = api_client.get("/matching/users", params={"team_id": team_id})
        if response.ok:
            return response.json()
        st.error(f"Failed to load matching users: {response.reason}")
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Error loading matching users: {exc}")
    return []


def fetch_matching_teams(circle_id: int) -> list[dict]:
    """Fetch matching team recommendations for the current user in a circle."""
    try:
        response = api_client.get("/matching/teams", params={"circle_id": circle_id})
        if response.ok:
            return response.json()
        st.error(f"Failed to load matching teams: {response.reason}")
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Error loading matching teams: {exc}")
    return []


def fetch_member_tags(circle_id: int, user_id: int) -> list[dict]:
    """Fetch another circle member's submitted tags."""
    try:
        response = api_client.get(f"/circles/{circle_id}/members/{user_id}/tags")
        if response.ok:
            return response.json()
        st.error(f"Failed to load member tags: {response.reason}")
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Error loading member tags: {exc}")
    return []


def get_cached_member_tags(
    tag_cache: dict[int, list[dict]],
    circle_id: int,
    user_id: int,
) -> list[dict]:
    """Return member tags using a page-local cache to avoid repeated requests."""
    if user_id not in tag_cache:
        tag_cache[user_id] = fetch_member_tags(circle_id, user_id)
    return tag_cache[user_id]


def build_match_explanation(match: dict) -> str:
    """Build a concise template-based explanation for a match result."""
    freedom_keywords = match.get("matched_freedom_keywords", []) or []
    if freedom_keywords:
        return f"Top keyword match: {', '.join(freedom_keywords)}"
    return "Strong overall match based on shared tag coverage."


def build_match_score_summary(match: dict) -> str:
    """Build a compact one-line numeric summary for a match card."""
    final_score = match.get("final_score", 0.0)
    coverage_score = match.get("coverage_score", 0.0)
    similarity_score = match.get("jaccard_score", 0.0)
    keyword_score = match.get("keyword_overlap_score", 0.0)
    return (
        f"Final {final_score:.2f} | Coverage {coverage_score:.2f} | "
        f"Similarity {similarity_score:.2f} | Keyword {keyword_score:.2f}"
    )


def get_stored_user_matches(selected_team_id: int) -> list[dict]:
    """Return persisted matching users for the currently selected team."""
    if st.session_state.get("matching_selected_team_id") != selected_team_id:
        return []
    return st.session_state.get("matching_user_results", []) or []


def split_user_teams(teams: Iterable[dict], user_id: int) -> Tuple[list[dict], list[dict]]:
    """Split teams into (created_by_user, joined_by_user) lists.

    A team is considered "created" when `creator_id == user_id`. A team is
    considered "joined" when `user_id` is present in `member_ids` but the
    team is not created by the user. This mirrors the logic used in tests
    and keeps the semantics explicit for the UI.
    """
    created: list[dict] = []
    joined: list[dict] = []

    for team in teams:
        creator_id = team.get("creator_id")
        member_ids = team.get("member_ids", []) or []
        if creator_id == user_id:
            created.append(team)
        elif user_id in member_ids:
            joined.append(team)

    return created, joined


def create_team(
    name: str,
    description: str,
    max_members: int,
    required_tags: list[str],
    required_tag_rules: list[dict],
    circle_id: int,
    freedom_requirement_text: str = "",
) -> tuple[bool, str]:
    """Create a team."""
    current_user = get_current_user()
    creator_id = current_user.get("id")
    if creator_id is None:
        return False, "Please log in again before creating a team."

    try:
        response = api_client.post(
            "/teams",
            data={
                "name": name,
                "description": description,
                "max_members": max_members,
                "required_tags": required_tags,
                "required_tag_rules": required_tag_rules,
                "circle_id": circle_id,
                "freedom_requirement_text": freedom_requirement_text,
            },
        )
        if response.ok:
            return True, "Team created successfully."
        return False, f"Failed to create team: {response.reason}"
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"Error creating team: {exc}"


def normalize_team_tag_definition(tag: dict) -> dict:
    """Normalize backend and mock tag definitions for team creation."""
    tag_data_type = tag.get("data_type") or tag.get("type") or "string"
    type_aliases = {
        "text": "string",
        "select": "single_select",
        "multiselect": "multi_select",
        "number": "integer",
    }
    normalized_type = type_aliases.get(tag_data_type, tag_data_type)
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


def build_team_requirement_mode_widget_key(circle_id: int, tag: dict) -> str:
    """Build a stable unique widget key for a team requirement mode control."""
    tag_id = tag.get("id")
    if tag_id is not None:
        return f"team_requirement_mode_{circle_id}_{tag_id}"
    return f"team_requirement_mode_{circle_id}_{tag.get('name', 'unknown')}"


def get_team_requirement_mode_label(mode: str) -> str:
    """Return a human-readable label for a requirement mode."""
    if mode == TEAM_REQUIREMENT_MODE_REQUIRED_ONLY:
        return "Required only"
    if mode == TEAM_REQUIREMENT_MODE_MATCH_VALUE:
        return "Must match value"
    return "Not required"


def should_collect_team_requirement_value(mode: str) -> bool:
    """Return whether the UI should collect a concrete expected value for this mode."""
    return mode == TEAM_REQUIREMENT_MODE_MATCH_VALUE


def validate_team_requirement_value(tag: dict, mode: str, value) -> tuple[bool, str]:
    """Validate a team requirement value before sending it."""
    if mode != TEAM_REQUIREMENT_MODE_MATCH_VALUE:
        return True, ""
    if value in (None, "", []):
        return False, f"{tag['name']} needs a value when set to Must match value."

    if tag.get("data_type") == "multi_select":
        max_selections = tag.get("max_selections")
        if max_selections is not None and len(value) > max_selections:
            return False, f"{tag['name']} allows at most {max_selections} selections."

    if is_numeric_team_requirement(tag):
        numeric_range = coerce_team_requirement_numeric_range_value(tag, value)
        try:
            min_value = parse_team_requirement_numeric_bound(tag, numeric_range.get("min"))
            max_value = parse_team_requirement_numeric_bound(tag, numeric_range.get("max"))
        except (TypeError, ValueError):
            if tag.get("data_type") == "integer":
                return False, f"{tag['name']} must be a whole number range."
            return False, f"{tag['name']} must be a numeric range."
        if min_value is not None and max_value is not None and min_value > max_value:
            return False, f"{tag['name']} must use a valid range where min is not greater than max."
        return True, ""

    return True, ""


def normalize_team_requirement_value(tag: dict, value):
    """Convert team requirement values to backend-compatible typed payloads."""
    if value in (None, "", []):
        return value

    if is_numeric_team_requirement(tag):
        numeric_range = coerce_team_requirement_numeric_range_value(tag, value)
        return {
            "min": parse_team_requirement_numeric_bound(tag, numeric_range.get("min")),
            "max": parse_team_requirement_numeric_bound(tag, numeric_range.get("max")),
        }

    if tag.get("data_type") == "integer":
        return int(value)

    if tag.get("data_type") == "float":
        return float(value)

    return value


def build_team_required_tags_payload(
    tag_definitions: list[dict],
    requirement_modes: dict[str, str],
    tag_data: dict,
) -> list[str]:
    """Build backend-compatible required_tags from schema-driven team inputs."""
    required_tags: list[str] = []
    for tag in tag_definitions:
        mode = requirement_modes.get(tag["name"], TEAM_REQUIREMENT_MODE_NOT_REQUIRED)
        if mode == TEAM_REQUIREMENT_MODE_NOT_REQUIRED:
            continue
        required_tags.append(tag["name"])
    return required_tags


def build_team_required_tag_rules_payload(
    tag_definitions: list[dict],
    requirement_modes: dict[str, str],
    tag_data: dict,
) -> list[dict]:
    """Build structured team requirement rules from schema-driven inputs."""
    required_tag_rules: list[dict] = []
    for tag in tag_definitions:
        mode = requirement_modes.get(tag["name"], TEAM_REQUIREMENT_MODE_NOT_REQUIRED)
        if mode != TEAM_REQUIREMENT_MODE_MATCH_VALUE:
            continue
        value = tag_data.get(tag["name"])
        if value in (None, "", []):
            continue
        normalized_value = normalize_team_requirement_value(tag, value)
        required_tag_rules.append(
            {
                "tag_name": tag["name"],
                "expected_value": normalized_value,
            }
        )
    return required_tag_rules


def build_team_requirement_widget_key(circle_id: int, tag: dict) -> str:
    """Build a stable unique widget key for a team requirement input."""
    tag_id = tag.get("id")
    if tag_id is not None:
        return f"team_requirement_{circle_id}_{tag_id}"
    return f"team_requirement_{circle_id}_{tag.get('name', 'unknown')}"


def can_view_team_member_sections(team: dict, user_id: Optional[int]) -> bool:
    """Return whether the user can see member-only sections in team detail."""
    if user_id is None:
        return False
    if team.get("creator_id") == user_id:
        return True
    return user_id in (team.get("member_ids", []) or [])


def send_invitation(team_id: int, user_id: int, team_name: str) -> tuple[bool, str]:
    """Send an invitation to a circle member."""
    try:
        response = api_client.post(
            f"/teams/{team_id}/invite",
            data={"user_id": user_id},
        )
        if response.ok:
            try:
                payload = response.json()
            except Exception:  # pragma: no cover - defensive
                payload = {}

            # Explicit failure if backend reports success == False
            if payload.get("success") is False:
                return False, payload.get("message", "Failed to send invitation.")

            # Mock/backend contract: if a status field is present and is not "pending",
            # treat it as a failure. If status is absent, consider the request successful.
            status = payload.get("status")
            if status is not None and status != "pending":
                return False, payload.get("message", "Failed to send invitation.")

            # Otherwise, treat the 2xx response as a success.
            return True, payload.get("message", "Invitation sent successfully.")

        detail = ""
        try:
            detail = response.json().get("detail", "")
        except Exception:
            detail = ""
        return False, detail or f"Failed to send invitation: {response.reason}"
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"Error sending invitation: {exc}"


def respond_to_invitation(invite_id: int, accept: bool) -> tuple[bool, str]:
    """Accept or reject an invitation."""
    try:
        response = api_client.post(
            f"/invitations/{invite_id}/respond",
            data={"accept": accept},
        )
        if response.ok:
            payload = response.json()
            return payload.get("success", False), payload.get("message", "Invitation updated.")
        return False, f"Failed to respond: {response.reason}"
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"Error responding to invitation: {exc}"


def request_to_join_team(team_id: int) -> tuple[bool, str]:
    """Submit a join request for the current user."""
    try:
        response = api_client.post(f"/teams/{team_id}/request-join")
        if response.ok:
            payload = response.json()
            return True, payload.get("message", "Join request sent.")

        detail = ""
        try:
            error_payload = response.json()
            detail = error_payload.get("detail") or error_payload.get("message", "")
        except Exception:
            detail = ""
        return False, detail or f"Failed to request to join: {response.reason}"
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"Error requesting to join: {exc}"


def format_member_tag_value(tag: dict) -> str:
    """Render stored tag values into a compact human-readable string."""
    raw_value = tag.get("value", "")
    tag_type = tag.get("data_type")

    if tag_type == "multi_select":
        try:
            parsed = json.loads(raw_value)
        except (TypeError, json.JSONDecodeError):
            return str(raw_value)
        if isinstance(parsed, list):
            return ", ".join(str(item) for item in parsed)
    if tag_type == "boolean":
        if str(raw_value).lower() in {"true", "1"}:
            return "Yes"
        if str(raw_value).lower() in {"false", "0"}:
            return "No"
    return str(raw_value)


def build_team_freedom_summary(team: dict) -> str:
    """Build a concise summary of a team's saved freedom requirement."""
    freedom_text = (team.get("freedom_requirement_text") or "").strip()
    freedom_keywords = team.get("freedom_requirement_profile_keywords", []) or []

    parts: list[str] = []
    if freedom_text:
        parts.append(freedom_text)
    if freedom_keywords:
        parts.append(f"Keywords: {', '.join(freedom_keywords)}")
    return " | ".join(parts)


def build_required_rules_summary(required_rules: list[dict]) -> str:
    """Build a concise caption-friendly summary for team required rules."""
    if not required_rules:
        return ""
    return ", ".join(
        f"{rule.get('tag_name')}={format_team_requirement_expected_value(rule.get('expected_value'))}"
        for rule in required_rules
    )


def is_numeric_team_requirement(tag: dict) -> bool:
    """Return whether this tag should use numeric range inputs."""
    return tag.get("data_type") in {"integer", "float"}


def parse_team_requirement_numeric_bound(tag: dict, raw_value):
    """Convert one numeric range bound into the correct type."""
    if raw_value in (None, ""):
        return None
    if tag.get("data_type") == "integer":
        return int(raw_value)
    return float(raw_value)


def coerce_team_requirement_numeric_range_value(tag: dict, value) -> dict[str, object]:
    """Normalize legacy scalar and new dict-shaped numeric inputs into one range object."""
    if isinstance(value, dict):
        return {
            "min": value.get("min"),
            "max": value.get("max"),
        }
    return {"min": value, "max": value}


def format_team_requirement_expected_value(expected_value) -> str:
    """Format one expected value for human-readable captions."""
    if isinstance(expected_value, dict) and ("min" in expected_value or "max" in expected_value):
        min_value = expected_value.get("min")
        max_value = expected_value.get("max")
        min_label = "-inf" if min_value is None else str(min_value)
        max_label = "+inf" if max_value is None else str(max_value)
        return f"[{min_label} ~ {max_label}]"
    return str(expected_value)


def split_invitations_for_management(
    invitations: list[dict], user_id: int
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Split inbox items into incoming invites, creator approvals, outgoing requests, and history."""
    incoming_invites = [
        invite
        for invite in invitations
        if invite.get("kind", "invite") == "invite"
        and invite.get("invitee_id") == user_id
        and invite.get("status") == "pending"
    ]
    incoming_requests = [
        invite
        for invite in invitations
        if invite.get("kind") == "join_request"
        and invite.get("invitee_id") == user_id
        and invite.get("inviter_id") != user_id
        and invite.get("status") == "pending"
    ]
    outgoing_requests = [
        invite
        for invite in invitations
        if invite.get("kind") == "join_request"
        and invite.get("inviter_id") == user_id
        and invite.get("status") == "pending"
    ]
    processed = [
        invite
        for invite in invitations
        if invite.get("status") != "pending"
        and (
            invite.get("invitee_id") == user_id
            or invite.get("inviter_id") == user_id
        )
    ]
    return incoming_invites, incoming_requests, outgoing_requests, processed


def render_team_detail() -> None:
    """Render a detailed view of the selected team."""
    circle_id = st.session_state.get("current_circle_id")
    if not circle_id:
        st.warning("Join a circle first to view team details.")
        return

    teams = fetch_teams(circle_id)
    team = get_selected_team(teams)
    if team is None:
        st.warning("Selected team was not found.")
        if st.button("\u2B05\uFE0F Back to Team Overview", key="back_missing_team_detail"):
            close_team_detail()
        return

    circle_members = fetch_circle_members(circle_id)
    current_user = get_current_user()
    current_user_id = current_user.get("id")
    member_lookup = {
        member.get("id"): member
        for member in circle_members
        if member.get("id") is not None
    }
    can_view_member_sections = can_view_team_member_sections(team, current_user_id)
    team_members = [
        member_lookup[user_id]
        for user_id in team.get("member_ids", []) or []
        if user_id in member_lookup
    ]
    member_tag_cache: dict[int, list[dict]] = {}

    if st.button("\u2B05\uFE0F Back to Team Overview", key=f"back_team_detail_{team.get('id')}"):
        close_team_detail()

    st.title(team.get("name", "Team Detail"))
    creator_label = team.get("creator_username") or "Unknown"
    st.markdown(f"**Creator:** {creator_label}")
    st.markdown(f"**Description:** {team.get('description', 'No description')}")
    st.markdown(
        f"**Status:** {team.get('status', 'Recruiting')} | "
        f"**Members:** {team.get('current_members', 0)}/{team.get('max_members', 0)}"
    )

    required_tags = team.get("required_tags", []) or []
    required_rules = team.get("required_tag_rules", []) or []
    if required_tags:
        st.caption(f"Required tags: {', '.join(required_tags)}")
    if required_rules:
        st.caption(f"Required rules: {build_required_rules_summary(required_rules)}")
    freedom_summary = build_team_freedom_summary(team)
    if freedom_summary:
        st.caption(f"Freedom requirement: {freedom_summary}")

    if not can_view_member_sections:
        st.warning("You must join this team before viewing its members or invitations.")
        return

    team_invitations = fetch_team_invitations(team["id"])

    st.markdown("---")
    st.subheader("Members")
    if not team_members:
        st.info("No members found for this team.")
    else:
        for member in team_members:
            with st.container(border=True):
                member_id = member.get("id")
                labels: list[str] = []
                if member_id == team.get("creator_id"):
                    labels.append("Creator")
                if member_id == current_user_id:
                    labels.append("You")
                suffix = f" ({', '.join(labels)})" if labels else ""
                info_col, action_col = st.columns([4, 1.4])
                with info_col:
                    st.markdown(f"**{member.get('username', 'Unknown')}**{suffix}")
                    st.caption(member.get("email", ""))
                    if member_id is not None:
                        member_tags = get_cached_member_tags(
                            member_tag_cache,
                            circle_id,
                            int(member_id),
                        )
                        if member_tags:
                            formatted_tags = [
                                f"{tag.get('tag_name', 'Tag')}: {format_member_tag_value(tag)}"
                                for tag in member_tags
                            ]
                            st.caption("Tags: " + " | ".join(formatted_tags))
                        else:
                            st.caption("Tags: none submitted")
                with action_col:
                    if member_id is not None and st.button(
                        "Profile",
                        key=f"team_member_profile_{team.get('id')}_{member_id}",
                    ):
                        open_public_profile(int(member_id))

    pending_team_invitations = [
        invite for invite in team_invitations if invite.get("status") == "pending"
    ]
    if pending_team_invitations:
        st.markdown("---")
        st.subheader("Pending Invitations")
        for invite in pending_team_invitations:
            invitee = member_lookup.get(invite.get("invitee_id"), {})
            invitee_label = invitee.get("username") or f"User #{invite.get('invitee_id')}"
            with st.container(border=True):
                info_col, action_col = st.columns([4, 1.4])
                with info_col:
                    st.markdown(f"**{invitee_label}**")
                    st.caption(invitee.get("email", ""))
                    invitee_id = invite.get("invitee_id")
                    if invitee_id is not None:
                        invitee_tags = get_cached_member_tags(
                            member_tag_cache,
                            circle_id,
                            int(invitee_id),
                        )
                        if invitee_tags:
                            formatted_tags = [
                                f"{tag.get('tag_name', 'Tag')}: {format_member_tag_value(tag)}"
                                for tag in invitee_tags
                            ]
                            st.caption("Tags: " + " | ".join(formatted_tags))
                        else:
                            st.caption("Tags: none submitted")
                with action_col:
                    if invitee_id is not None and st.button(
                        "Profile",
                        key=f"pending_invitee_profile_{team.get('id')}_{invitee_id}",
                    ):
                        open_public_profile(int(invitee_id))

    st.markdown("---")
    st.subheader("Invite Members")
    st.caption("You can also invite directly from Matching.")
    member_ids = set(team.get("member_ids", []) or [])
    pending_lookup = {
        (invite.get("team_id"), invite.get("invitee_id"))
        for invite in team_invitations
        if invite.get("status") == "pending"
    }
    candidate_members = [
        member
        for member in circle_members
        if member.get("id") is not None
        and member.get("id") not in member_ids
        and (team.get("id"), member.get("id")) not in pending_lookup
    ]

    if not candidate_members:
        st.info("No eligible circle members available to invite.")
        return

    options = {
        f"{member.get('username', 'user')} ({member.get('email', '')})": member.get("id")
        for member in candidate_members
    }
    with st.form(f"team_detail_invite_form_{team.get('id')}"):
        selected_member = st.selectbox(
            "Invite a circle member",
            options=list(options.keys()),
        )
        invite_submitted = st.form_submit_button("\u2709\uFE0F Send Invitation", type="primary")
        if invite_submitted:
            selected_user_id = options[selected_member]
            team_id = team.get("id")
            if team_id is None or selected_user_id is None:
                st.error("Unable to send invitation because team or user data is incomplete.")
            else:
                success, message = send_invitation(
                    team_id=int(team_id),
                    user_id=int(selected_user_id),
                    team_name=team.get("name", "Team"),
                )
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)


def render_team_list() -> None:
    """Render all teams in the current circle."""
    st.header("Teams in This Circle")
    current_user = get_current_user()
    current_user_id = current_user.get("id")

    circle_id = st.session_state.get("current_circle_id")
    if not circle_id:
        st.warning("Join a circle first to view teams.")
        if st.button("\U0001F3E0 Go to Circle Hall", key="go_circle_hall_list"):
            st.switch_page("pages/circles.py")
        return

    teams = fetch_teams(circle_id)
    if not teams:
        st.info("No teams yet. Create the first one.")
        return

    st.markdown(f"**Total Teams: {len(teams)}**")
    for team in teams:
        with st.container(border=True):
            col_left, col_status, col_action = st.columns([3, 1, 1])
            with col_left:
                st.markdown(f"**{team.get('name', 'Unnamed Team')}**")
                creator_label = team.get("creator_username") or "Unknown"
                st.caption(f"Creator: {creator_label}")
                st.write(team.get("description", "No description"))
                required_tags = team.get("required_tags", [])
                if required_tags:
                    st.caption(f"Required tags: {', '.join(required_tags)}")
                required_rules = team.get("required_tag_rules", []) or []
                required_rules_summary = build_required_rules_summary(required_rules)
                if required_rules_summary:
                    st.caption(f"Required rules: {required_rules_summary}")
            with col_status:
                status = team.get("status", "Recruiting")
                members = team.get("current_members", 0)
                max_members = team.get("max_members", 0)
                if status == "Recruiting":
                    st.success(status)
                else:
                    st.error(status)
                st.caption(f"Members: {members}/{max_members}")
            with col_action:
                if st.button("\U0001F50D View Details", key=f"team_list_detail_{team.get('id')}"):
                    team_id = team.get("id")
                    if team_id is not None:
                        open_team_detail(int(team_id))
                member_ids = team.get("member_ids", []) or []
                is_joinable = (
                    team.get("status") == "Recruiting"
                    and team.get("current_members", 0) < team.get("max_members", 0)
                )
                if current_user_id in member_ids:
                    st.caption("You are already in this team")
                elif is_joinable:
                    st.caption("Open to join requests")
                    st.caption("Use Matching to send a request to the creator")
                else:
                    st.caption("Not accepting members")




def render_create_team() -> None:
    """Render the team creation form with split value/mode controls."""
    st.header("Create Team")

    circle_id = st.session_state.get("current_circle_id")
    if not circle_id:
        st.warning("Join a circle first to create a team.")
        if st.button("Go to Circle Hall", key="go_circle_hall_create_v2"):
            st.switch_page("pages/circles.py")
        return

    team_name = st.text_input("Team Name *", max_chars=50, key=f"team_name_{circle_id}")
    team_description = st.text_area("Description", max_chars=500, key=f"team_description_{circle_id}")
    max_members = st.selectbox(
        "Max Members",
        options=[2, 3, 4, 5, 6, 7, 8],
        index=3,
        key=f"team_max_members_{circle_id}",
    )
    tag_definitions = [normalize_team_tag_definition(tag) for tag in fetch_circle_tags(circle_id)]
    team_requirement_modes: dict[str, str] = {}
    team_requirement_values: dict[str, object] = {}

    if tag_definitions:
        st.caption("Left sets the value. Right decides whether the tag is ignored, required, or must match.")
        for tag in tag_definitions:
            tag_name = tag["name"]
            tag_type = tag["data_type"]
            tag_options = tag.get("options")
            mode_key = build_team_requirement_mode_widget_key(circle_id, tag)
            widget_key = build_team_requirement_widget_key(circle_id, tag)
            value_col, mode_col = st.columns([5, 2])

            with mode_col:
                selected_mode = st.selectbox(
                    "Requirement",
                    options=TEAM_REQUIREMENT_MODE_OPTIONS,
                    format_func=get_team_requirement_mode_label,
                    key=mode_key,
                )
            team_requirement_modes[tag_name] = selected_mode

            with value_col:
                if selected_mode == TEAM_REQUIREMENT_MODE_NOT_REQUIRED:
                    st.text_input(
                        tag_name,
                        value="Not required",
                        disabled=True,
                        key=f"{widget_key}_disabled",
                    )
                    team_requirement_values[tag_name] = ""
                elif selected_mode == TEAM_REQUIREMENT_MODE_REQUIRED_ONLY:
                    st.text_input(
                        tag_name,
                        value="Any value accepted",
                        disabled=True,
                        key=f"{widget_key}_required_only",
                    )
                    team_requirement_values[tag_name] = ""
                elif tag_type in ("single_select", "enum") and tag_options:
                    team_requirement_values[tag_name] = st.selectbox(
                        tag_name,
                        options=tag_options,
                        key=widget_key,
                    )
                elif tag_type == "multi_select" and tag_options:
                    help_text = None
                    if tag.get("max_selections") is not None:
                        help_text = f"Select up to {tag['max_selections']} options."
                    team_requirement_values[tag_name] = st.multiselect(
                        tag_name,
                        options=tag_options,
                        help=help_text,
                        key=widget_key,
                    )
                elif tag_type == "boolean":
                    team_requirement_values[tag_name] = st.checkbox(
                        tag_name,
                        value=False,
                        key=widget_key,
                    )
                elif is_numeric_team_requirement(tag):
                    st.markdown(f"**{tag_name}**")
                    min_col, separator_col, max_col = st.columns([5, 1, 5])
                    with min_col:
                        min_value = st.text_input(
                            "Min",
                            placeholder="-inf",
                            key=f"{widget_key}_min",
                        )
                    with separator_col:
                        st.markdown(
                            "<div style='text-align:center;padding-top:2rem;'>~</div>",
                            unsafe_allow_html=True,
                        )
                    with max_col:
                        max_value = st.text_input(
                            "Max",
                            placeholder="+inf",
                            key=f"{widget_key}_max",
                        )
                    team_requirement_values[tag_name] = {
                        "min": min_value.strip(),
                        "max": max_value.strip(),
                    }
                else:
                    team_requirement_values[tag_name] = st.text_input(
                        tag_name,
                        placeholder="Enter the expected value",
                        key=widget_key,
                    )
    else:
        st.info("No circle tag definitions found. Team requirements will be empty.")

    freedom_requirement_text = st.text_area(
        "Freedom Tag Requirements (optional)",
        placeholder="Describe what you're looking for in free text. e.g., Looking for someone passionate about AI and creative projects",
        max_chars=500,
        key=f"freedom_requirement_{circle_id}",
    )

    submitted = st.button("Create Team", type="primary", key=f"create_team_submit_{circle_id}")

    if submitted:
        if not team_name.strip():
            st.error("Team name is required.")
            return

        validation_errors = []
        for tag in tag_definitions:
            is_valid, error_message = validate_team_requirement_value(
                tag,
                team_requirement_modes.get(tag["name"], TEAM_REQUIREMENT_MODE_NOT_REQUIRED),
                team_requirement_values.get(tag["name"]),
            )
            if not is_valid:
                validation_errors.append(error_message)

        if validation_errors:
            st.error(" ".join(validation_errors))
            return

        required_tags = build_team_required_tags_payload(
            tag_definitions,
            team_requirement_modes,
            team_requirement_values,
        )
        required_tag_rules = build_team_required_tag_rules_payload(
            tag_definitions,
            team_requirement_modes,
            team_requirement_values,
        )

        success, message = create_team(
            name=team_name.strip(),
            description=team_description.strip(),
            max_members=max_members,
            required_tags=required_tags,
            required_tag_rules=required_tag_rules,
            circle_id=circle_id,
            freedom_requirement_text=freedom_requirement_text.strip(),
        )
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)


def render_my_teams() -> None:
    """Render the current user's teams and received invitations."""
    st.header("My Teams")

    current_user = get_current_user()
    user_id = current_user.get("id")
    circle_id = st.session_state.get("current_circle_id")

    if not circle_id:
        st.warning("Join a circle first to view your teams.")
        return
    if user_id is None:
        st.warning("Please log in again.")
        return

    teams = fetch_teams(circle_id)
    created_teams, joined_teams = split_user_teams(teams, user_id)

    st.subheader("Teams I Created")
    if not created_teams:
        st.info("You have not created any teams yet.")
    else:
        for team in created_teams:
            with st.container(border=True):
                st.markdown(f"**{team.get('name', 'Unnamed Team')}**")
                creator_label = team.get("creator_username") or "Unknown"
                st.caption(f"Creator: {creator_label}")
                st.caption(team.get("description", "No description"))
                required_tags = team.get("required_tags", []) or []
                if required_tags:
                    st.caption(f"Required tags: {', '.join(required_tags)}")
                required_rules_summary = build_required_rules_summary(
                    team.get("required_tag_rules", []) or []
                )
                if required_rules_summary:
                    st.caption(f"Required rules: {required_rules_summary}")
                st.write(
                    f"Members: {team.get('current_members', 0)}/{team.get('max_members', 0)}"
                )
                if st.button("\U0001F50D View Details", key=f"my_created_team_detail_{team.get('id')}"):
                    team_id = team.get("id")
                    if team_id is not None:
                        open_team_detail(int(team_id))

    st.markdown("---")
    st.subheader("Teams I Joined")
    if not joined_teams:
        st.info("You have not joined any teams yet.")
    else:
        for team in joined_teams:
            with st.container(border=True):
                st.markdown(f"**{team.get('name', 'Unnamed Team')}**")
                creator_label = team.get("creator_username") or "Unknown"
                st.caption(f"Creator: {creator_label}")
                st.caption(team.get("description", "No description"))
                required_tags = team.get("required_tags", []) or []
                if required_tags:
                    st.caption(f"Required tags: {', '.join(required_tags)}")
                required_rules_summary = build_required_rules_summary(
                    team.get("required_tag_rules", []) or []
                )
                if required_rules_summary:
                    st.caption(f"Required rules: {required_rules_summary}")
                st.write(
                    f"Members: {team.get('current_members', 0)}/{team.get('max_members', 0)}"
                )
                if st.button("\U0001F50D View Details", key=f"my_joined_team_detail_{team.get('id')}"):
                    team_id = team.get("id")
                    if team_id is not None:
                        open_team_detail(int(team_id))


def render_invitation_management() -> None:
    """Render invitation actions and history."""
    st.header("Invitation Management")

    current_user = get_current_user()
    user_id = current_user.get("id")
    circle_id = st.session_state.get("current_circle_id")
    if user_id is None:
        st.warning("Please log in again.")
        return

    invitations = fetch_invitations()
    pending, pending_requests, outgoing_requests, processed = split_invitations_for_management(
        invitations, user_id
    )

    st.subheader("Pending Invitations")
    if not pending:
        st.info("No pending invitations.")
    else:
        for invite in pending:
            with st.container(border=True):
                team_display = invite.get("team_name") or f"Team #{invite.get('team_id')}"
                st.markdown(f"**{team_display}**")
                st.caption(f"Invited by user {invite.get('inviter_id')}")

                accept_col, reject_col = st.columns(2)
                with accept_col:
                    if st.button(
                        "\u2705 Accept",
                        key=f"accept_invitation_{invite.get('id')}",
                        type="primary",
                    ):
                        invite_id = invite.get("id")
                        if invite_id is None:
                            st.error("Unable to respond because invitation data is incomplete.")
                            continue
                        success, message = respond_to_invitation(invite_id, True)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                with reject_col:
                    render_button_variant_marker("danger")
                    if st.button("\u274C Reject", key=f"reject_invitation_{invite.get('id')}"):
                        invite_id = invite.get("id")
                        if invite_id is None:
                            st.error("Unable to respond because invitation data is incomplete.")
                            continue
                        success, message = respond_to_invitation(invite_id, False)
                        if success:
                            st.info(message)
                            st.rerun()
                        else:
                            st.error(message)

    st.markdown("---")
    st.subheader("Join Requests To Review")
    if not pending_requests:
        st.info("No join requests waiting for your approval.")
    else:
        for invite in pending_requests:
            with st.container(border=True):
                team_display = invite.get("team_name") or f"Team #{invite.get('team_id')}"
                requester_label = invite.get("inviter_username") or f"User #{invite.get('inviter_id')}"
                requester_id = invite.get("inviter_id")
                st.markdown(f"**{team_display}**")
                st.caption(f"Requested by {requester_label}")
                if requester_id is not None and circle_id is not None:
                    requester_tags = fetch_member_tags(circle_id, int(requester_id))
                    if requester_tags:
                        formatted_tags = [
                            f"{tag.get('tag_name', 'Tag')}: {format_member_tag_value(tag)}"
                            for tag in requester_tags
                        ]
                        st.write("Tags: " + " | ".join(formatted_tags))
                    else:
                        st.caption("Tags: none submitted")

                profile_col, approve_col, reject_col = st.columns(3)
                with profile_col:
                    if requester_id is not None and st.button(
                        "\U0001F464 View Profile",
                        key=f"view_join_request_profile_{invite.get('id')}",
                    ):
                        open_public_profile(int(requester_id))
                with approve_col:
                    if st.button(
                        "\u2705 Approve",
                        key=f"approve_join_request_{invite.get('id')}",
                        type="primary",
                    ):
                        invite_id = invite.get("id")
                        if invite_id is None:
                            st.error("Unable to respond because request data is incomplete.")
                            continue
                        success, message = respond_to_invitation(invite_id, True)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                with reject_col:
                    render_button_variant_marker("danger")
                    if st.button("\u274C Reject", key=f"reject_join_request_{invite.get('id')}"):
                        invite_id = invite.get("id")
                        if invite_id is None:
                            st.error("Unable to respond because request data is incomplete.")
                            continue
                        success, message = respond_to_invitation(invite_id, False)
                        if success:
                            st.info(message)
                            st.rerun()
                        else:
                            st.error(message)

    st.markdown("---")
    st.subheader("My Join Requests")
    if not outgoing_requests:
        st.info("You have not requested to join any teams.")
    else:
        for invite in outgoing_requests:
            with st.container(border=True):
                team_display = invite.get("team_name") or f"Team #{invite.get('team_id')}"
                creator_label = invite.get("invitee_username") or f"User #{invite.get('invitee_id')}"
                st.markdown(f"**{team_display}**")
                st.caption(f"Waiting for {creator_label} to respond")

    st.markdown("---")
    st.subheader("Invitation History")
    if not processed:
        st.info("No invitation history.")
    else:
        for invite in processed:
            with st.container(border=True):
                col_left, col_right = st.columns([3, 1])
                with col_left:
                    team_display = invite.get("team_name") or f"Team #{invite.get('team_id')}"
                    st.markdown(f"**{team_display}**")
                    kind_label = "Join request" if invite.get("kind") == "join_request" else "Invitation"
                    st.caption(f"{kind_label} status: {invite.get('status', 'unknown')}")
                with col_right:
                    if invite.get("status") == "accepted":
                        st.success("Accepted")
                    else:
                        st.error("Rejected")


def render_matching_section() -> None:
    """Render matching-based recommendations for teams and users."""
    current_user = get_current_user()
    user_id = current_user.get("id")
    if user_id is None:
        st.warning("Please log in again.")
        return

    circle_id = st.session_state.get("current_circle_id")
    if not circle_id:
        st.info("Join a circle first to use matching recommendations.")
        return

    st.subheader("Recommend members for my team")
    teams = fetch_teams(circle_id)

    my_teams = [
        team
        for team in teams
        if user_id in team.get("member_ids", [])
        or team.get("creator_id") == user_id
    ]

    if not my_teams:
        st.info("You are not a member or creator of any teams in this circle yet.")
    else:
        team_labels = [
            f"{team.get('name', 'Unnamed')} (members {team.get('current_members', 0)}/"
            f"{team.get('max_members', 0)})"
            for team in my_teams
        ]
        selected_label = st.selectbox(
            "Select a team to find potential members",
            options=team_labels,
        )
        selected_team = my_teams[team_labels.index(selected_label)]
        matches = get_stored_user_matches(selected_team["id"])
        has_requested_matches = st.session_state.get("matching_requested", False)

        if st.button("\U0001F465 Get user recommendations", type="primary"):
            matches = fetch_matching_users(selected_team["id"])
            has_requested_matches = True
            st.session_state.matching_requested = True
            st.session_state.matching_selected_team_id = selected_team["id"]
            st.session_state.matching_user_results = matches

        if not has_requested_matches:
            st.caption("Choose a team and request recommendations to view candidate members.")
        elif not matches:
            st.info("No matching users found yet.")
        else:
            for match in matches:
                with st.container(border=True):
                    info_col, profile_col, invite_col = st.columns([4, 1, 1])
                    with info_col:
                        st.markdown(
                            f"**{match.get('username', 'Unknown user')}** "
                            f"({match.get('email', 'N/A')})"
                        )
                        st.caption(build_match_score_summary(match))
                        matched = ", ".join(match.get("matched_tags", [])) or "-"
                        missing = ", ".join(match.get("missing_required_tags", [])) or "-"
                        st.write(f"Matched tags: {matched}")
                        st.write(f"Missing required tags: {missing}")
                        st.caption(build_match_explanation(match))
                    with profile_col:
                        if st.button(
                            "Profile",
                            key=f"matching_profile_{selected_team['id']}_{match['user_id']}",
                        ):
                            open_public_profile(int(match["user_id"]))
                    with invite_col:
                        if st.button(
                            "Invite",
                            key=f"invite_match_{selected_team['id']}_{match['user_id']}",
                            type="primary",
                        ):
                            success, message = send_invitation(
                                selected_team["id"],
                                match["user_id"],
                                selected_team.get("name", "Team"),
                            )
                            if success:
                                st.success(message)
                            else:
                                st.error(message)

    st.markdown("---")
    st.subheader("Recommend teams for me")
    st.caption("You can send a join request directly to the team creator from here.")

    if st.button("\U0001F50E Find teams for me", key="find_matching_teams", type="primary"):
        matches = fetch_matching_teams(circle_id)
        if not matches:
            st.info("No matching teams found yet.")
        else:
            for item in matches:
                team = item.get("team", {})
                with st.container(border=True):
                    info_col, action_col = st.columns([4, 1])
                    with info_col:
                        st.markdown(f"**{team.get('name', 'Unnamed Team')}**")
                        creator_label = team.get("creator_username") or "Unknown"
                        st.caption(f"Creator: {creator_label}")
                        st.caption(team.get("description", "No description"))
                        st.write(
                            f"Members: {team.get('current_members', 0)}/"
                            f"{team.get('max_members', 0)}"
                        )
                        st.caption(build_match_score_summary(item))
                        missing = ", ".join(item.get("missing_required_tags", [])) or "-"
                        st.write(f"Missing required tags: {missing}")
                        st.caption(build_match_explanation(item))
                    with action_col:
                        team_id = team.get("id")
                        member_ids = team.get("member_ids", []) or []
                        is_joinable = (
                            team.get("status") == "Recruiting"
                            and user_id not in member_ids
                            and team_id is not None
                        )
                        if user_id in member_ids:
                            st.caption("Already joined")
                        elif is_joinable and st.button(
                            "Request to Join",
                            key=f"request_join_match_{team_id}",
                            type="primary",
                        ):
                            success, message = request_to_join_team(int(team_id))
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                        elif not is_joinable:
                            st.caption("Unavailable")


def main() -> None:
    """Render the team management page."""
    apply_button_usability_style()

    st.title("Team Management")
    st.markdown("Create teams, invite members, and manage invitations.")

    require_auth()

    if not st.session_state.get("current_circle_id"):
        st.warning("Join a circle first to access team management.")
        if st.button("\U0001F3E0 Go to Circle Hall", key="go_circle_hall_main"):
            go_to_circle_hall()
        return

    if not can_access_current_circle(st.session_state["current_circle_id"]):
        if st.button("\U0001F3E0 Go to Circle Hall", key="go_circle_hall_forbidden"):
            go_to_circle_hall()
        return

    nav_col1 = st.columns(1)[0]
    with nav_col1:
        if st.button("\u2B05\uFE0F Back to Circle Detail", key="back_to_circle_detail_from_team"):
            go_to_circle_detail()
    if st.session_state.get("team_management_focus_detail"):
        render_team_detail()
        return

    team_tab, create_tab, my_tab, invitation_tab, matching_tab = st.tabs(
        ["Team List", "Create Team", "My Teams", "Invitations", "Matching"]
    )
    with team_tab:
        render_team_list()
    with create_tab:
        render_create_team()
    with my_tab:
        render_my_teams()
    with invitation_tab:
        render_invitation_management()
    with matching_tab:
        render_matching_section()


if __name__ == "__main__":
    main()

