from fastapi.testclient import TestClient

from scripts.seed_data import PASSWORD, seed_dataset
from src.main import app


client = TestClient(app)


def login_seed_user(identifier: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": identifier, "password": PASSWORD},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def find_by_name(items: list[dict], name: str) -> dict:
    for item in items:
        if item["name"] == name:
            return item
    raise AssertionError(f"Item not found: {name}")


def find_by_username(items: list[dict], username: str) -> dict:
    for item in items:
        if item["username"] == username:
            return item
    raise AssertionError(f"User not found: {username}")


def test_demo_seed_supports_invitation_and_matching_flow(db_session):
    seed_dataset(db_session, "demo")

    alice_headers = login_seed_user("seed_demo_alice")
    clara_headers = login_seed_user("seed_demo_clara")

    circles_response = client.get("/circles/", headers=alice_headers)
    assert circles_response.status_code == 200
    circles = circles_response.json()
    ai_circle = find_by_name(circles, "[SEED DEMO] AI Capstone Showcase")

    teams_response = client.get(f"/circles/{ai_circle['id']}/teams", headers=alice_headers)
    assert teams_response.status_code == 200
    teams = teams_response.json()
    vision_builders = find_by_name(teams, "[SEED DEMO] Vision Builders")
    assert vision_builders["current_members"] == 2

    members_response = client.get(
        f"/circles/{ai_circle['id']}/members",
        headers=alice_headers,
    )
    assert members_response.status_code == 200
    clara = find_by_username(members_response.json(), "seed_demo_clara")

    match_response = client.get(
        f"/matching/users?team_id={vision_builders['id']}",
        headers=alice_headers,
    )
    assert match_response.status_code == 200
    matched_usernames = [item["username"] for item in match_response.json()]
    assert "seed_demo_derek" in matched_usernames
    assert "seed_demo_clara" in matched_usernames

    invite_response = client.post(
        f"/teams/{vision_builders['id']}/invite",
        headers=alice_headers,
        json={"user_id": clara["id"], "team_name": vision_builders["name"]},
    )
    assert invite_response.status_code == 201
    invitation = invite_response.json()
    assert invitation["status"] == "pending"

    inbox_response = client.get("/invitations", headers=clara_headers)
    assert inbox_response.status_code == 200
    inbox = inbox_response.json()
    pending_ids = {item["id"] for item in inbox if item["status"] == "pending"}
    assert invitation["id"] in pending_ids

    accept_response = client.post(
        f"/invitations/{invitation['id']}/respond",
        headers=clara_headers,
        json={"accept": True},
    )
    assert accept_response.status_code == 200
    assert accept_response.json()["team_status"] == "Recruiting"

    refreshed_teams_response = client.get(
        f"/circles/{ai_circle['id']}/teams",
        headers=alice_headers,
    )
    assert refreshed_teams_response.status_code == 200
    refreshed_team = find_by_name(
        refreshed_teams_response.json(),
        "[SEED DEMO] Vision Builders",
    )
    assert refreshed_team["current_members"] == 3


def test_stress_seed_pending_invitation_can_lock_team(db_session):
    seed_dataset(db_session, "stress")

    hazel_headers = login_seed_user("seed_stress_hazel")
    amir_headers = login_seed_user("seed_stress_amir")

    inbox_response = client.get("/invitations", headers=hazel_headers)
    assert inbox_response.status_code == 200
    inbox = inbox_response.json()
    pending = next(
        item
        for item in inbox
        if item["status"] == "pending"
    )

    respond_response = client.post(
        f"/invitations/{pending['id']}/respond",
        headers=hazel_headers,
        json={"accept": True},
    )
    assert respond_response.status_code == 200
    assert respond_response.json()["team_status"] == "Locked"

    circles_response = client.get("/circles/", headers=amir_headers)
    assert circles_response.status_code == 200
    systems_lab = find_by_name(circles_response.json(), "[SEED STRESS] Systems Lab")

    teams_response = client.get(
        f"/circles/{systems_lab['id']}/teams",
        headers=amir_headers,
    )
    assert teams_response.status_code == 200
    alpha_team = find_by_name(teams_response.json(), "[SEED STRESS] Systems Lab Alpha")
    assert alpha_team["status"] == "Locked"
    assert alpha_team["current_members"] == 4

    matching_response = client.get(
        f"/matching/teams?circle_id={systems_lab['id']}",
        headers=hazel_headers,
    )
    assert matching_response.status_code == 200
    team_names = [item["team"]["name"] for item in matching_response.json()]
    assert "[SEED STRESS] Systems Lab Alpha" not in team_names


def test_stress_seed_matching_scores_are_not_uniform(db_session):
    seed_dataset(db_session, "stress")

    amir_headers = login_seed_user("seed_stress_amir")

    circles_response = client.get("/circles/", headers=amir_headers)
    assert circles_response.status_code == 200
    systems_lab = find_by_name(circles_response.json(), "[SEED STRESS] Systems Lab")

    teams_response = client.get(
        f"/circles/{systems_lab['id']}/teams",
        headers=amir_headers,
    )
    assert teams_response.status_code == 200
    alpha_team = find_by_name(teams_response.json(), "[SEED STRESS] Systems Lab Alpha")

    match_response = client.get(
        f"/matching/users?team_id={alpha_team['id']}",
        headers=amir_headers,
    )
    assert match_response.status_code == 200
    matches = match_response.json()
    assert matches
    assert any(item["coverage_score"] < 1.0 or item["jaccard_score"] < 1.0 for item in matches)
    assert all("freedom_score" in item for item in matches)
    assert all("matched_freedom_keywords" in item for item in matches)
    assert all(item["freedom_score"] >= 0.0 for item in matches)


def test_stress_seed_for_amir_has_non_zero_keyword_overlap_candidates(db_session):
    seed_dataset(db_session, "stress")

    amir_headers = login_seed_user("seed_stress_amir")

    circles_response = client.get("/circles/", headers=amir_headers)
    assert circles_response.status_code == 200
    systems_lab = find_by_name(circles_response.json(), "[SEED STRESS] Systems Lab")

    teams_response = client.get(
        f"/circles/{systems_lab['id']}/teams",
        headers=amir_headers,
    )
    assert teams_response.status_code == 200
    alpha_team = find_by_name(teams_response.json(), "[SEED STRESS] Systems Lab Alpha")

    match_response = client.get(
        f"/matching/users?team_id={alpha_team['id']}",
        headers=amir_headers,
    )
    assert match_response.status_code == 200
    matches = match_response.json()
    assert matches
    assert any(item["keyword_overlap_score"] > 0.0 for item in matches)


def test_stress_seed_manual_invite_reaches_diana_and_duplicate_is_blocked(db_session):
    seed_dataset(db_session, "stress")

    amir_headers = login_seed_user("seed_stress_amir")
    diana_headers = login_seed_user("seed_stress_diana")

    circles_response = client.get("/circles/", headers=amir_headers)
    assert circles_response.status_code == 200
    systems_lab = find_by_name(circles_response.json(), "[SEED STRESS] Systems Lab")

    teams_response = client.get(
        f"/circles/{systems_lab['id']}/teams",
        headers=amir_headers,
    )
    assert teams_response.status_code == 200
    alpha_team = find_by_name(teams_response.json(), "[SEED STRESS] Systems Lab Alpha")

    members_response = client.get(
        f"/circles/{systems_lab['id']}/members",
        headers=amir_headers,
    )
    assert members_response.status_code == 200
    diana = find_by_username(members_response.json(), "seed_stress_diana")

    first_invite_response = client.post(
        f"/teams/{alpha_team['id']}/invite",
        headers=amir_headers,
        json={"user_id": diana["id"], "team_name": alpha_team["name"]},
    )
    assert first_invite_response.status_code == 201
    invitation = first_invite_response.json()

    duplicate_invite_response = client.post(
        f"/teams/{alpha_team['id']}/invite",
        headers=amir_headers,
        json={"user_id": diana["id"], "team_name": alpha_team["name"]},
    )
    assert duplicate_invite_response.status_code == 409
    assert duplicate_invite_response.json()["detail"] == "Invitation already pending"

    inbox_response = client.get("/invitations", headers=diana_headers)
    assert inbox_response.status_code == 200
    pending_ids = {item["id"] for item in inbox_response.json() if item["status"] == "pending"}
    assert invitation["id"] in pending_ids


def test_demo_seed_invitation_can_be_rejected_without_joining_team(db_session):
    seed_dataset(db_session, "demo")

    alice_headers = login_seed_user("seed_demo_alice")
    derek_headers = login_seed_user("seed_demo_derek")

    circles_response = client.get("/circles/", headers=alice_headers)
    assert circles_response.status_code == 200
    ai_circle = find_by_name(circles_response.json(), "[SEED DEMO] AI Capstone Showcase")

    teams_response = client.get(
        f"/circles/{ai_circle['id']}/teams",
        headers=alice_headers,
    )
    assert teams_response.status_code == 200
    vision_builders = find_by_name(teams_response.json(), "[SEED DEMO] Vision Builders")
    assert vision_builders["current_members"] == 2
    assert vision_builders["status"] == "Recruiting"

    members_response = client.get(
        f"/circles/{ai_circle['id']}/members",
        headers=alice_headers,
    )
    assert members_response.status_code == 200
    derek = find_by_username(members_response.json(), "seed_demo_derek")

    inbox_response = client.get("/invitations", headers=derek_headers)
    assert inbox_response.status_code == 200
    pending = next(
        item
        for item in inbox_response.json()
        if item["team_id"] == vision_builders["id"] and item["status"] == "pending"
    )

    reject_response = client.post(
        f"/invitations/{pending['id']}/respond",
        headers=derek_headers,
        json={"accept": False},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["success"] is True
    assert reject_response.json()["team_status"] == "Recruiting"

    refreshed_inbox_response = client.get("/invitations", headers=derek_headers)
    assert refreshed_inbox_response.status_code == 200
    rejected = next(
        item
        for item in refreshed_inbox_response.json()
        if item["id"] == pending["id"]
    )
    assert rejected["status"] == "rejected"

    refreshed_teams_response = client.get(
        f"/circles/{ai_circle['id']}/teams",
        headers=alice_headers,
    )
    assert refreshed_teams_response.status_code == 200
    refreshed_team = find_by_name(
        refreshed_teams_response.json(),
        "[SEED DEMO] Vision Builders",
    )
    assert refreshed_team["current_members"] == 2
    assert refreshed_team["status"] == "Recruiting"
    assert derek["id"] not in refreshed_team["member_ids"]


def test_demo_seed_member_can_leave_team_and_become_candidate_again(db_session):
    seed_dataset(db_session, "demo")

    alice_headers = login_seed_user("seed_demo_alice")
    clara_headers = login_seed_user("seed_demo_clara")

    circles_response = client.get("/circles/", headers=alice_headers)
    assert circles_response.status_code == 200
    ai_circle = find_by_name(circles_response.json(), "[SEED DEMO] AI Capstone Showcase")

    teams_response = client.get(
        f"/circles/{ai_circle['id']}/teams",
        headers=alice_headers,
    )
    assert teams_response.status_code == 200
    vision_builders = find_by_name(teams_response.json(), "[SEED DEMO] Vision Builders")

    members_response = client.get(
        f"/circles/{ai_circle['id']}/members",
        headers=alice_headers,
    )
    assert members_response.status_code == 200
    clara = find_by_username(members_response.json(), "seed_demo_clara")

    invite_response = client.post(
        f"/teams/{vision_builders['id']}/invite",
        headers=alice_headers,
        json={"user_id": clara["id"], "team_name": vision_builders["name"]},
    )
    assert invite_response.status_code == 201
    invitation = invite_response.json()

    accept_response = client.post(
        f"/invitations/{invitation['id']}/respond",
        headers=clara_headers,
        json={"accept": True},
    )
    assert accept_response.status_code == 200

    leave_response = client.delete(
        f"/teams/{vision_builders['id']}/leave",
        headers=clara_headers,
    )
    assert leave_response.status_code == 204

    refreshed_teams_response = client.get(
        f"/circles/{ai_circle['id']}/teams",
        headers=alice_headers,
    )
    assert refreshed_teams_response.status_code == 200
    refreshed_team = find_by_name(
        refreshed_teams_response.json(),
        "[SEED DEMO] Vision Builders",
    )
    assert refreshed_team["current_members"] == 2
    assert clara["id"] not in refreshed_team["member_ids"]

    match_response = client.get(
        f"/matching/users?team_id={vision_builders['id']}",
        headers=alice_headers,
    )
    assert match_response.status_code == 200
    matched_usernames = [item["username"] for item in match_response.json()]
    assert "seed_demo_clara" in matched_usernames


def test_stress_seed_locked_team_unlocks_when_member_leaves(db_session):
    seed_dataset(db_session, "stress")

    hazel_headers = login_seed_user("seed_stress_hazel")
    amir_headers = login_seed_user("seed_stress_amir")

    inbox_response = client.get("/invitations", headers=hazel_headers)
    assert inbox_response.status_code == 200
    pending = next(
        item
        for item in inbox_response.json()
        if item["status"] == "pending"
    )

    accept_response = client.post(
        f"/invitations/{pending['id']}/respond",
        headers=hazel_headers,
        json={"accept": True},
    )
    assert accept_response.status_code == 200
    assert accept_response.json()["team_status"] == "Locked"

    leave_response = client.delete(
        f"/teams/{pending['team_id']}/leave",
        headers=hazel_headers,
    )
    assert leave_response.status_code == 204

    circles_response = client.get("/circles/", headers=amir_headers)
    assert circles_response.status_code == 200
    systems_lab = find_by_name(circles_response.json(), "[SEED STRESS] Systems Lab")

    teams_response = client.get(
        f"/circles/{systems_lab['id']}/teams",
        headers=amir_headers,
    )
    assert teams_response.status_code == 200
    alpha_team = find_by_name(teams_response.json(), "[SEED STRESS] Systems Lab Alpha")
    assert alpha_team["status"] == "Recruiting"
    assert alpha_team["current_members"] == 3

    matching_response = client.get(
        f"/matching/teams?circle_id={systems_lab['id']}",
        headers=hazel_headers,
    )
    assert matching_response.status_code == 200
    team_names = [item["team"]["name"] for item in matching_response.json()]
    assert "[SEED STRESS] Systems Lab Alpha" in team_names


def test_seed_join_request_is_visible_to_creator_and_can_be_approved(db_session):
    seed_dataset(db_session, "demo")

    alice_headers = login_seed_user("seed_demo_alice")
    eva_headers = login_seed_user("seed_demo_eva")

    creator_inbox_response = client.get("/invitations", headers=alice_headers)
    assert creator_inbox_response.status_code == 200
    creator_inbox = creator_inbox_response.json()
    join_request = next(
        item
        for item in creator_inbox
        if item["kind"] == "join_request"
        and item["status"] == "pending"
        and item["inviter_username"] == "seed_demo_eva"
    )

    respond_response = client.post(
        f"/invitations/{join_request['id']}/respond",
        headers=alice_headers,
        json={"accept": True},
    )
    assert respond_response.status_code == 200
    assert respond_response.json()["success"] is True

    circles_response = client.get("/circles/", headers=alice_headers)
    assert circles_response.status_code == 200
    ai_circle = find_by_name(circles_response.json(), "[SEED DEMO] AI Capstone Showcase")

    teams_response = client.get(f"/circles/{ai_circle['id']}/teams", headers=alice_headers)
    assert teams_response.status_code == 200
    vision_builders = find_by_name(teams_response.json(), "[SEED DEMO] Vision Builders")

    members_response = client.get(f"/circles/{ai_circle['id']}/members", headers=alice_headers)
    assert members_response.status_code == 200
    eva = find_by_username(members_response.json(), "seed_demo_eva")

    assert eva["id"] in vision_builders["member_ids"]

    requester_inbox_response = client.get("/invitations", headers=eva_headers)
    assert requester_inbox_response.status_code == 200
    requester_record = next(
        item
        for item in requester_inbox_response.json()
        if item["id"] == join_request["id"]
    )
    assert requester_record["status"] == "accepted"
