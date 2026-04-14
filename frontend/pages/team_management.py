"""    
Team management page.

Provides team listing, creation, invitation sending, invitation handling,
plus matching-based recommendations.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Tuple

import streamlit as st


parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.api import api_client
from utils.auth import get_current_user, init_session_state, require_auth


init_session_state()

st.set_page_config(
    page_title="Team Management - Boundary Circle",
    page_icon="👥",
)


def fetch_teams(circle_id: int) -> list[dict]:
    """Fetch teams for a circle."""
    try:
        response = api_client.get(f"/circles/{circle_id}/teams")
        if response.ok:
            return response.json()
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
        st.error(f"Failed to load members: {response.reason}")
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Error loading members: {exc}")
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
    circle_id: int,
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
                "circle_id": circle_id,
            },
        )
        if response.ok:
            return True, "Team created successfully."
        return False, f"Failed to create team: {response.reason}"
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"Error creating team: {exc}"


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

        return False, f"Failed to send invitation: {response.reason}"
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


def render_team_list() -> None:
    """Render all teams in the current circle."""
    st.header("Teams in This Circle")

    circle_id = st.session_state.get("current_circle_id")
    if not circle_id:
        st.warning("Join a circle first to view teams.")
        if st.button("Go to Circle Hall", key="go_circle_hall_list"):
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
                st.write(team.get("description", "No description"))
                required_tags = team.get("required_tags", [])
                if required_tags:
                    st.caption(f"Required tags: {', '.join(required_tags)}")
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
                is_joinable = (
                    team.get("status") == "Recruiting"
                    and team.get("current_members", 0) < team.get("max_members", 0)
                )
                if is_joinable:
                    st.button("Open for invites", key=f"open_{team.get('id')}", disabled=True)
                    st.caption("Join via invitation")
                else:
                    st.caption("Not accepting members")


def render_create_team() -> None:
    """Render the team creation form."""
    st.header("Create Team")

    circle_id = st.session_state.get("current_circle_id")
    if not circle_id:
        st.warning("Join a circle first to create a team.")
        if st.button("Go to Circle Hall", key="go_circle_hall_create"):
            st.switch_page("pages/circles.py")
        return

    with st.form("create_team_form"):
        team_name = st.text_input("Team Name *", max_chars=50)
        team_description = st.text_area("Description", max_chars=500)
        max_members = st.selectbox(
            "Max Members",
            options=[2, 3, 4, 5, 6, 7, 8],
            index=3,
        )
        required_tags = st.multiselect(
            "Required Tags (Optional)",
            options=["skill", "availability", "role", "experience", "interest"],
        )
        submitted = st.form_submit_button("Create Team", type="primary")

        if submitted:
            if not team_name.strip():
                st.error("Team name is required.")
                return

            success, message = create_team(
                name=team_name.strip(),
                description=team_description.strip(),
                max_members=max_members,
                required_tags=required_tags,
                circle_id=circle_id,
            )
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)


def render_my_teams() -> None:
    """Render the current user's teams and invitation sender."""
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
    invitations = fetch_invitations()
    created_teams, joined_teams = split_user_teams(teams, user_id)

    pending_received = [
        invite
        for invite in invitations
        if invite.get("invitee_id") == user_id and invite.get("status") == "pending"
    ]
    pending_lookup = {
        (invite.get("team_id"), invite.get("invitee_id"))
        for invite in invitations
        if invite.get("status") == "pending"
    }

    st.subheader("Teams I Created")
    if not created_teams:
        st.info("You have not created any teams yet.")
    else:
        circle_members = fetch_circle_members(circle_id)
        for team in created_teams:
            with st.container(border=True):
                st.markdown(f"**{team.get('name', 'Unnamed Team')}**")
                st.caption(team.get("description", "No description"))
                st.write(
                    f"Members: {team.get('current_members', 0)}/{team.get('max_members', 0)}"
                )

                member_ids = set(team.get("member_ids", []))
                candidate_members = [
                    member
                    for member in circle_members
                    if member.get("id") != user_id
                    and member.get("id") not in member_ids
                    and (team.get("id"), member.get("id")) not in pending_lookup
                ]

                if not candidate_members:
                    st.caption("No members available to invite.")
                    continue

                options = {
                    f"{member.get('username', 'user')} ({member.get('email', '')})": member.get("id")
                    for member in candidate_members
                }
                with st.form(f"invite_form_{team.get('id')}"):
                    selected_member = st.selectbox(
                        "Invite a circle member",
                        options=list(options.keys()),
                    )
                    invite_submitted = st.form_submit_button("Send Invitation")
                    if invite_submitted:
                        team_id = team.get("id")
                        selected_user_id = options[selected_member]
                        if team_id is None or selected_user_id is None:
                            st.error("Unable to send invitation because team data is incomplete.")
                            continue
                        success, message = send_invitation(
                            team_id=team_id,
                            user_id=selected_user_id,
                            team_name=team.get("name", "Team"),
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

    st.markdown("---")
    st.subheader("Teams I Joined")
    if not joined_teams:
        st.info("You have not joined any teams yet.")
    else:
        for team in joined_teams:
            with st.container(border=True):
                st.markdown(f"**{team.get('name', 'Unnamed Team')}**")
                st.caption(team.get("description", "No description"))
                st.write(
                    f"Members: {team.get('current_members', 0)}/{team.get('max_members', 0)}"
                )

    st.markdown("---")
    st.subheader("Pending Invitations")
    if not pending_received:
        st.info("No pending invitations.")
    else:
        for invite in pending_received:
            with st.container(border=True):
                st.markdown(f"**{invite.get('team_name', 'Unknown Team')}**")
                st.caption(f"Invited by user {invite.get('inviter_id')}")


def render_invitation_management() -> None:
    """Render invitation actions and history."""
    st.header("Invitation Management")

    current_user = get_current_user()
    user_id = current_user.get("id")
    if user_id is None:
        st.warning("Please log in again.")
        return

    invitations = fetch_invitations()
    pending = [
        invite
        for invite in invitations
        if invite.get("invitee_id") == user_id and invite.get("status") == "pending"
    ]
    processed = [
        invite
        for invite in invitations
        if invite.get("invitee_id") == user_id and invite.get("status") != "pending"
    ]

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
                        "Accept",
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
                    if st.button("Reject", key=f"reject_invitation_{invite.get('id')}"):
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
                    st.caption(f"Status: {invite.get('status', 'unknown')}")
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

        if st.button("Get user recommendations", type="primary"):
            matches = fetch_matching_users(selected_team["id"])
            if not matches:
                st.info("No matching users found yet.")
            else:
                for match in matches:
                    with st.container(border=True):
                        st.markdown(
                            f"**{match.get('username', 'Unknown user')}** "
                            f"({match.get('email', 'N/A')})"
                        )
                        cov = match.get("coverage_score", 0.0)
                        jac = match.get("jaccard_score", 0.0)
                        st.caption(
                            f"Coverage: {cov:.2f} · Similarity: {jac:.2f}"
                        )
                        matched = ", ".join(match.get("matched_tags", [])) or "-"
                        missing = ", ".join(match.get("missing_required_tags", [])) or "-"
                        st.write(f"Matched tags: {matched}")
                        st.write(f"Missing required tags: {missing}")

                        if st.button(
                            "Invite to team",
                            key=f"invite_match_{selected_team['id']}_{match['user_id']}",
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

    if st.button("Find teams for me", key="find_matching_teams", type="primary"):
        matches = fetch_matching_teams(circle_id)
        if not matches:
            st.info("No matching teams found yet.")
        else:
            for item in matches:
                team = item.get("team", {})
                with st.container(border=True):
                    st.markdown(f"**{team.get('name', 'Unnamed Team')}**")
                    st.caption(team.get("description", "No description"))
                    st.write(
                        f"Members: {team.get('current_members', 0)}/"
                        f"{team.get('max_members', 0)}"
                    )
                    cov = item.get("coverage_score", 0.0)
                    jac = item.get("jaccard_score", 0.0)
                    st.caption(
                        f"Coverage: {cov:.2f} · Similarity: {jac:.2f}"
                    )
                    missing = ", ".join(item.get("missing_required_tags", [])) or "-"
                    st.write(f"Missing required tags: {missing}")


def main() -> None:
    """Render the team management page."""
    st.title("Team Management")
    st.markdown("Create teams, invite members, and manage invitations.")

    require_auth()

    if not st.session_state.get("current_circle_id"):
        st.warning("Join a circle first to access team management.")
        if st.button("Go to Circle Hall", key="go_circle_hall_main"):
            st.switch_page("pages/circles.py")
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
