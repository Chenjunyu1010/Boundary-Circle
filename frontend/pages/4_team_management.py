"""    
Team management page.

Provides team listing, creation, invitation sending, and invitation handling.
"""

import sys
from pathlib import Path

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
    except Exception as exc:
        st.error(f"Error loading teams: {exc}")
    return []


def fetch_circle_members(circle_id: int) -> list[dict]:
    """Fetch circle members."""
    try:
        response = api_client.get(f"/circles/{circle_id}/members")
        if response.ok:
            return response.json()
        st.error(f"Failed to load members: {response.reason}")
    except Exception as exc:
        st.error(f"Error loading members: {exc}")
    return []


def fetch_invitations() -> list[dict]:
    """Fetch invitations related to the current user."""
    try:
        response = api_client.get("/invitations")
        if response.ok:
            return response.json()
        st.error(f"Failed to load invitations: {response.reason}")
    except Exception as exc:
        st.error(f"Error loading invitations: {exc}")
    return []


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
                "creator_id": creator_id,
            },
        )
        if response.ok:
            return True, "Team created successfully."
        return False, f"Failed to create team: {response.reason}"
    except Exception as exc:
        return False, f"Error creating team: {exc}"


def send_invitation(team_id: int, user_id: int, team_name: str) -> tuple[bool, str]:
    """Send an invitation to a circle member."""
    try:
        response = api_client.post(
            f"/teams/{team_id}/invite",
            data={"user_id": user_id, "team_name": team_name},
        )
        if response.ok:
            try:
                payload = response.json()
            except Exception:
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
    except Exception as exc:
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
    except Exception as exc:
        return False, f"Error responding to invitation: {exc}"


def split_user_teams(teams: list[dict], user_id: int) -> tuple[list[dict], list[dict]]:
    """Split teams into created teams and joined teams for the current user."""
    created_teams = [team for team in teams if team.get("creator_id") == user_id]
    joined_teams = [
        team
        for team in teams
        if team.get("creator_id") != user_id and user_id in team.get("member_ids", [])
    ]
    return created_teams, joined_teams


def render_team_list() -> None:
    """Render all teams in the current circle."""
    st.header("Teams in This Circle")

    circle_id = st.session_state.get("current_circle_id")
    if not circle_id:
        st.warning("Join a circle first to view teams.")
        if st.button("Go to Circle Hall", key="go_circle_hall_list"):
            st.switch_page("pages/2_Circles.py")
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
            st.switch_page("pages/2_Circles.py")
        return

    with st.form("create_team_form"):
        team_name = st.text_input("Team Name *", max_chars=50)
        team_description = st.text_area("Description", max_chars=500)
        max_members = st.selectbox("Max Members", options=[2, 3, 4, 5, 6, 7, 8], index=3)
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
                        success, message = send_invitation(
                            team_id=team.get("id"),
                            user_id=options[selected_member],
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
                st.markdown(f"**{invite.get('team_name', 'Unknown Team')}**")
                st.caption(f"Invited by user {invite.get('inviter_id')}")

                accept_col, reject_col = st.columns(2)
                with accept_col:
                    if st.button(
                        "Accept",
                        key=f"accept_invitation_{invite.get('id')}",
                        type="primary",
                    ):
                        success, message = respond_to_invitation(invite.get("id"), True)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                with reject_col:
                    if st.button("Reject", key=f"reject_invitation_{invite.get('id')}"):
                        success, message = respond_to_invitation(invite.get("id"), False)
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
                    st.markdown(f"**{invite.get('team_name', 'Unknown Team')}**")
                    st.caption(f"Status: {invite.get('status', 'unknown')}")
                with col_right:
                    if invite.get("status") == "accepted":
                        st.success("Accepted")
                    else:
                        st.error("Rejected")


def main() -> None:
    """Render the team management page."""
    st.title("Team Management")
    st.markdown("Create teams, invite members, and manage invitations.")

    require_auth()

    if not st.session_state.get("current_circle_id"):
        st.warning("Join a circle first to access team management.")
        if st.button("Go to Circle Hall", key="go_circle_hall_main"):
            st.switch_page("pages/2_Circles.py")
        return

    team_tab, create_tab, my_tab, invitation_tab = st.tabs(
        ["Team List", "Create Team", "My Teams", "Invitations"]
    )
    with team_tab:
        render_team_list()
    with create_tab:
        render_create_team()
    with my_tab:
        render_my_teams()
    with invitation_tab:
        render_invitation_management()


if __name__ == "__main__":
    main()
