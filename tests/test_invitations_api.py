from fastapi.testclient import TestClient

from src.api.teams import build_invitation_reads
from src.main import app
from src.models.core import User
from src.models.tags import CircleMember, CircleRole
from src.models.teams import Invitation, InvitationKind, InvitationStatus, Team, TeamMember


client = TestClient(app)


def register_and_login(username: str, email: str) -> tuple[dict, dict]:
    register_response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "secret123",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "secret123"},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return register_response.json(), headers


def add_circle_member(circle_id: int, user_id: int) -> CircleMember:
    return CircleMember(user_id=user_id, circle_id=circle_id, role=CircleRole.MEMBER)


def test_team_creator_can_send_invitation(db_session):
    creator, creator_headers = register_and_login("captain", "captain@example.com")
    invitee, _ = register_and_login("invitee", "invitee@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Invite Circle", "description": "Circle for invitations"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], invitee["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Invite Team",
            "description": "Team for invites",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    invitation_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )

    assert invitation_response.status_code == 201
    payload = invitation_response.json()
    assert payload["team_id"] == team["id"]
    assert payload["invitee_id"] == invitee["id"]
    assert payload["status"] == "pending"


def test_team_member_can_send_invitation(db_session):
    creator, creator_headers = register_and_login("creator2", "creator2@example.com")
    member, member_headers = register_and_login("member2", "member2@example.com")
    invitee, _ = register_and_login("invitee2", "invitee2@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Restricted Invite Circle", "description": "Circle for auth checks"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], member["id"]))
    db_session.add(add_circle_member(circle["id"], invitee["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Restricted Team",
            "description": "Team for auth checks",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    db_session.add(TeamMember(team_id=team["id"], user_id=member["id"]))
    db_session.commit()

    invitation_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=member_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )

    assert invitation_response.status_code == 201
    payload = invitation_response.json()
    assert payload["team_id"] == team["id"]
    assert payload["inviter_id"] == member["id"]
    assert payload["invitee_id"] == invitee["id"]


def test_non_team_member_cannot_send_invitation(db_session):
    creator, creator_headers = register_and_login("captain3", "captain3@example.com")
    outsider, outsider_headers = register_and_login("outsider3", "outsider3@example.com")
    invitee, _ = register_and_login("invitee3", "invitee3@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Unauthorized Invite Circle", "description": "Only team members can invite"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], invitee["id"]))
    db_session.add(add_circle_member(circle["id"], outsider["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Unauthorized Invite Team",
            "description": "Team with guarded invitations",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    invitation_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=outsider_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )

    assert invitation_response.status_code == 403
    assert invitation_response.json()["detail"] == "Only team creator or members can send invitations"


def test_duplicate_pending_invitation_is_rejected(db_session):
    creator, creator_headers = register_and_login("captain4", "captain4@example.com")
    invitee, _ = register_and_login("invitee4", "invitee4@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Duplicate Invite Circle", "description": "Duplicate invitation checks"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], invitee["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Duplicate Invite Team",
            "description": "Team for duplicate invites",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    first_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )
    second_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Invitation already pending"


def test_duplicate_pending_invitation_does_not_duplicate_invitee_inbox(db_session):
    creator, creator_headers = register_and_login("captain4b", "captain4b@example.com")
    invitee, invitee_headers = register_and_login("invitee4b", "invitee4b@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Duplicate Inbox Circle", "description": "Duplicate inbox checks"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], invitee["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Duplicate Inbox Team",
            "description": "Team for duplicate inbox checks",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    first_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )
    second_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    inbox_response = client.get("/invitations", headers=invitee_headers)
    assert inbox_response.status_code == 200
    inbox_items = [
        item
        for item in inbox_response.json()
        if item["team_id"] == team["id"] and item["status"] == "pending"
    ]
    assert len(inbox_items) == 1


def test_inviting_nonexistent_user_fails(db_session):
    creator, creator_headers = register_and_login("captain5", "captain5@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Missing Invitee Circle", "description": "Invitee existence check"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Missing Invitee Team",
            "description": "Team for nonexistent user checks",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    invitation_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": 999999, "team_name": team["name"]},
    )

    assert invitation_response.status_code in {403, 404}


def test_cross_circle_member_cannot_be_invited(db_session):
    creator, creator_headers = register_and_login("boundarycaptain", "boundarycaptain@example.com")
    invitee, invitee_headers = register_and_login("crosscircleuser", "crosscircleuser@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Boundary Circle A", "description": "Invite boundary checks"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    other_circle_response = client.post(
        "/circles/",
        headers=invitee_headers,
        json={"name": "Boundary Circle B", "description": "Separate circle"},
    )
    assert other_circle_response.status_code == 201

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Boundary Team",
            "description": "Should not invite outsiders",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    invitation_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )

    assert invitation_response.status_code == 403
    assert invitation_response.json()["detail"] == "Invitee must be a member of the same circle"


def test_invitations_endpoint_returns_received_only(db_session):
    creator, creator_headers = register_and_login("receivedcreator", "receivedcreator@example.com")
    invitee, invitee_headers = register_and_login("receivedinvitee", "receivedinvitee@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Received Invitations Circle", "description": "Circle for invitation inbox"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], invitee["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Received Team",
            "description": "Team for received-only invitation list",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    invitation_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )
    assert invitation_response.status_code == 201
    invitation = invitation_response.json()

    sender_invitations_response = client.get("/invitations", headers=creator_headers)
    assert sender_invitations_response.status_code == 200
    assert sender_invitations_response.json() == []

    receiver_invitations_response = client.get("/invitations", headers=invitee_headers)
    assert receiver_invitations_response.status_code == 200
    receiver_invitations = receiver_invitations_response.json()
    assert len(receiver_invitations) == 1
    assert receiver_invitations[0]["id"] == invitation["id"]
    assert receiver_invitations[0]["invitee_id"] == invitee["id"]


def test_accept_invitation_adds_team_member(db_session):
    creator, creator_headers = register_and_login("acceptcaptain", "acceptcaptain@example.com")
    invitee, invitee_headers = register_and_login("acceptmember", "acceptmember@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Accept Circle", "description": "Circle for acceptance flow"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], invitee["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Accept Team",
            "description": "Team to accept into",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    invitation_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )
    assert invitation_response.status_code == 201
    invitation = invitation_response.json()

    respond_response = client.post(
        f"/invitations/{invitation['id']}/respond",
        headers=invitee_headers,
        json={"accept": True},
    )
    assert respond_response.status_code == 200
    assert respond_response.json()["success"] is True

    teams_response = client.get(f"/circles/{circle['id']}/teams", headers=creator_headers)
    assert teams_response.status_code == 200
    stored_team = teams_response.json()[0]
    assert stored_team["current_members"] == 2
    assert invitee["id"] in stored_team["member_ids"]


def test_reject_invitation_keeps_team_recruiting(db_session):
    creator, creator_headers = register_and_login("rejectcaptain", "rejectcaptain@example.com")
    invitee, invitee_headers = register_and_login("rejectmember", "rejectmember@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Reject Circle", "description": "Circle for rejection flow"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], invitee["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Reject Team",
            "description": "Team to reject",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    invitation_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )
    assert invitation_response.status_code == 201
    invitation = invitation_response.json()

    respond_response = client.post(
        f"/invitations/{invitation['id']}/respond",
        headers=invitee_headers,
        json={"accept": False},
    )
    assert respond_response.status_code == 200
    assert respond_response.json()["success"] is True

    teams_response = client.get(f"/circles/{circle['id']}/teams", headers=creator_headers)
    stored_team = teams_response.json()[0]
    assert stored_team["current_members"] == 1
    assert stored_team["status"] == "Recruiting"


def test_team_auto_locks_when_full(db_session):
    creator, creator_headers = register_and_login("lockcaptain", "lockcaptain@example.com")
    invitee, invitee_headers = register_and_login("lockmember", "lockmember@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Lock Circle", "description": "Circle for locking flow"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], invitee["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Lock Team",
            "description": "Team that should lock",
            "circle_id": circle["id"],
            "max_members": 2,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    invitation_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )
    assert invitation_response.status_code == 201
    invitation = invitation_response.json()

    respond_response = client.post(
        f"/invitations/{invitation['id']}/respond",
        headers=invitee_headers,
        json={"accept": True},
    )
    assert respond_response.status_code == 200
    assert respond_response.json()["team_status"] == "Locked"

    teams_response = client.get(f"/circles/{circle['id']}/teams", headers=creator_headers)
    stored_team = teams_response.json()[0]
    assert stored_team["status"] == "Locked"
    assert stored_team["current_members"] == 2


def test_accept_invitation_rejects_when_team_is_full(db_session):
    creator, creator_headers = register_and_login("fullcaptain", "fullcaptain@example.com")
    invitee_a, invitee_a_headers = register_and_login("fullmembera", "fullmembera@example.com")
    invitee_b, invitee_b_headers = register_and_login("fullmemberb", "fullmemberb@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Full Team Circle", "description": "Capacity guard checks"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], invitee_a["id"]))
    db_session.add(add_circle_member(circle["id"], invitee_b["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Capacity Team",
            "description": "Should stop at max members",
            "circle_id": circle["id"],
            "max_members": 2,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    invitation_a_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee_a["id"], "team_name": team["name"]},
    )
    invitation_b_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee_b["id"], "team_name": team["name"]},
    )
    assert invitation_a_response.status_code == 201
    assert invitation_b_response.status_code == 201
    invitation_a = invitation_a_response.json()
    invitation_b = invitation_b_response.json()

    accept_a_response = client.post(
        f"/invitations/{invitation_a['id']}/respond",
        headers=invitee_a_headers,
        json={"accept": True},
    )
    assert accept_a_response.status_code == 200
    assert accept_a_response.json()["team_status"] == "Locked"

    accept_b_response = client.post(
        f"/invitations/{invitation_b['id']}/respond",
        headers=invitee_b_headers,
        json={"accept": True},
    )

    assert accept_b_response.status_code == 409
    assert accept_b_response.json()["detail"] == "Team is already full"


def test_circle_member_can_request_to_join_team(db_session):
    creator, creator_headers = register_and_login("requestcaptain", "requestcaptain@example.com")
    requester, requester_headers = register_and_login("requestmember", "requestmember@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Join Request Circle", "description": "Circle for join-request flow"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], requester["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Join Request Team",
            "description": "Team accepting join requests",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    request_response = client.post(
        f"/teams/{team['id']}/request-join",
        headers=requester_headers,
    )

    assert request_response.status_code == 201
    payload = request_response.json()
    assert payload["team_id"] == team["id"]
    assert payload["inviter_id"] == requester["id"]
    assert payload["invitee_id"] == creator["id"]
    assert payload["kind"] == "join_request"
    assert payload["status"] == "pending"


def test_non_circle_member_cannot_request_to_join_team(db_session):
    creator, creator_headers = register_and_login("requestcaptain2", "requestcaptain2@example.com")
    requester, requester_headers = register_and_login("requestoutsider2", "requestoutsider2@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Join Boundary Circle", "description": "Circle join boundary checks"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Boundary Join Team",
            "description": "Team guarded by circle membership",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    request_response = client.post(
        f"/teams/{team['id']}/request-join",
        headers=requester_headers,
    )

    assert request_response.status_code == 403
    assert request_response.json()["detail"] == "Requester must be a member of the same circle"


def test_duplicate_join_request_overwrites_previous_pending_request(db_session):
    creator, creator_headers = register_and_login("requestcaptain3", "requestcaptain3@example.com")
    requester, requester_headers = register_and_login("requestmember3", "requestmember3@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Repeat Join Circle", "description": "Circle for repeated join requests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], requester["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Repeat Join Team",
            "description": "Team for repeated join requests",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    first_response = client.post(
        f"/teams/{team['id']}/request-join",
        headers=requester_headers,
    )
    second_response = client.post(
        f"/teams/{team['id']}/request-join",
        headers=requester_headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    creator_invitations_response = client.get("/invitations", headers=creator_headers)
    assert creator_invitations_response.status_code == 200
    creator_pending = [
        item
        for item in creator_invitations_response.json()
        if item["team_id"] == team["id"]
        and item["kind"] == "join_request"
        and item["status"] == "pending"
    ]
    assert len(creator_pending) == 1
    assert creator_pending[0]["id"] == second_response.json()["id"]


def test_invitations_endpoint_includes_join_requests_for_team_creator(db_session):
    creator, creator_headers = register_and_login("requestcaptain4", "requestcaptain4@example.com")
    requester, requester_headers = register_and_login("requestmember4", "requestmember4@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Creator Inbox Circle", "description": "Circle for creator inbox"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], requester["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Creator Inbox Team",
            "description": "Team whose creator reviews requests",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    request_response = client.post(
        f"/teams/{team['id']}/request-join",
        headers=requester_headers,
    )
    assert request_response.status_code == 201

    creator_invitations_response = client.get("/invitations", headers=creator_headers)
    requester_invitations_response = client.get("/invitations", headers=requester_headers)

    assert creator_invitations_response.status_code == 200
    assert requester_invitations_response.status_code == 200

    creator_items = creator_invitations_response.json()
    requester_items = requester_invitations_response.json()

    assert any(
        item["team_id"] == team["id"]
        and item["kind"] == "join_request"
        and item["invitee_id"] == creator["id"]
        for item in creator_items
    )
    assert any(
        item["team_id"] == team["id"]
        and item["kind"] == "join_request"
        and item["inviter_id"] == requester["id"]
        for item in requester_items
    )


def test_only_team_creator_can_respond_to_join_request(db_session):
    creator, creator_headers = register_and_login("requestcaptain5", "requestcaptain5@example.com")
    member, member_headers = register_and_login("requestmember5", "requestmember5@example.com")
    requester, requester_headers = register_and_login("requestuser5", "requestuser5@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Join Approval Circle", "description": "Circle for join-request approvals"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], member["id"]))
    db_session.add(add_circle_member(circle["id"], requester["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Join Approval Team",
            "description": "Team with creator-only approvals",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    db_session.add(TeamMember(team_id=team["id"], user_id=member["id"]))
    db_session.commit()

    request_response = client.post(
        f"/teams/{team['id']}/request-join",
        headers=requester_headers,
    )
    assert request_response.status_code == 201
    join_request = request_response.json()

    member_respond_response = client.post(
        f"/invitations/{join_request['id']}/respond",
        headers=member_headers,
        json={"accept": True},
    )
    requester_respond_response = client.post(
        f"/invitations/{join_request['id']}/respond",
        headers=requester_headers,
        json={"accept": True},
    )

    assert member_respond_response.status_code == 403
    assert member_respond_response.json()["detail"] == "Only the team creator can respond"
    assert requester_respond_response.status_code == 403
    assert requester_respond_response.json()["detail"] == "Only the team creator can respond"


def test_team_creator_can_accept_join_request_and_add_member(db_session):
    creator, creator_headers = register_and_login("requestcaptain6", "requestcaptain6@example.com")
    requester, requester_headers = register_and_login("requestmember6", "requestmember6@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Join Accept Circle", "description": "Circle for accepting join requests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], requester["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Join Accept Team",
            "description": "Team that accepts join requests",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    request_response = client.post(
        f"/teams/{team['id']}/request-join",
        headers=requester_headers,
    )
    assert request_response.status_code == 201
    join_request = request_response.json()

    respond_response = client.post(
        f"/invitations/{join_request['id']}/respond",
        headers=creator_headers,
        json={"accept": True},
    )

    assert respond_response.status_code == 200
    assert respond_response.json()["success"] is True
    assert respond_response.json()["message"] == "Join request accepted"

    teams_response = client.get(f"/circles/{circle['id']}/teams", headers=creator_headers)
    assert teams_response.status_code == 200
    stored_team = teams_response.json()[0]
    assert requester["id"] in stored_team["member_ids"]
    assert stored_team["current_members"] == 2


def test_team_creator_can_reject_join_request_without_adding_member(db_session):
    creator, creator_headers = register_and_login("requestcaptain7", "requestcaptain7@example.com")
    requester, requester_headers = register_and_login("requestmember7", "requestmember7@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Join Reject Circle", "description": "Circle for rejecting join requests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(add_circle_member(circle["id"], requester["id"]))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Join Reject Team",
            "description": "Team that rejects join requests",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    request_response = client.post(
        f"/teams/{team['id']}/request-join",
        headers=requester_headers,
    )
    assert request_response.status_code == 201
    join_request = request_response.json()

    respond_response = client.post(
        f"/invitations/{join_request['id']}/respond",
        headers=creator_headers,
        json={"accept": False},
    )

    assert respond_response.status_code == 200
    assert respond_response.json()["success"] is True
    assert respond_response.json()["message"] == "Join request rejected"

    teams_response = client.get(f"/circles/{circle['id']}/teams", headers=creator_headers)
    stored_team = teams_response.json()[0]
    assert requester["id"] not in stored_team["member_ids"]
    assert stored_team["current_members"] == 1


def test_build_invitation_reads_can_use_preloaded_related_records(db_session):
    creator, _ = register_and_login("batchcaptain", "batchcaptain@example.com")
    invitee, _ = register_and_login("batchinvitee", "batchinvitee@example.com")
    team = Team(name="Batch Team", description="Batch read team", circle_id=1, creator_id=creator["id"], max_members=4)
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)

    invitation = Invitation(
        team_id=team.id,
        inviter_id=creator["id"],
        invitee_id=invitee["id"],
        kind=InvitationKind.INVITE,
        status=InvitationStatus.PENDING,
    )
    db_session.add(invitation)
    db_session.commit()
    db_session.refresh(invitation)

    original_get = db_session.get

    def fail_related_get(model, identity, *args, **kwargs):
        if model in {Team, User}:
            raise AssertionError("session.get should not be used for preloaded Team/User records")
        return original_get(model, identity, *args, **kwargs)

    db_session.get = fail_related_get
    try:
        payload = build_invitation_reads(
            [invitation],
            db_session,
            teams_by_id={team.id: team},
            users_by_id={
                creator["id"]: original_get(User, creator["id"]),
                invitee["id"]: original_get(User, invitee["id"]),
            },
        )
    finally:
        db_session.get = original_get

    assert len(payload) == 1
    assert payload[0].team_name == "Batch Team"
    assert payload[0].inviter_username == "batchcaptain"
    assert payload[0].invitee_username == "batchinvitee"
