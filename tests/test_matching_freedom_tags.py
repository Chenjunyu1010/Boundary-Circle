from __future__ import annotations

from typing import Tuple

from fastapi.testclient import TestClient
import pytest
from sqlmodel import select

from src.main import app
from src.services import matching as matching_service
from src.models.tags import CircleMember, CircleRole, TagDataType, TagDefinition, UserTag
from src.models.teams import Team


client = TestClient(app)


def _update_circle_member_freedom(db_session, user_id: int, circle_id: int, freedom_tag_text: str, freedom_tag_profile_json: str) -> None:
    """Helper to update freedom profile on CircleMember using SQLModel session pattern."""
    circle_member = db_session.exec(
        select(CircleMember).filter_by(user_id=user_id, circle_id=circle_id)
    ).first()
    if circle_member:
        circle_member.freedom_tag_text = freedom_tag_text
        circle_member.freedom_tag_profile_json = freedom_tag_profile_json
        db_session.add(circle_member)
        db_session.commit()


def _update_team_freedom(db_session, team_id: int, freedom_requirement_profile_json: str) -> None:
    """Helper to update freedom requirement profile on Team using SQLModel session pattern."""
    team = db_session.exec(select(Team).filter_by(id=team_id)).first()
    if team:
        team.freedom_requirement_profile_json = freedom_requirement_profile_json
        db_session.add(team)
        db_session.commit()


def register_and_login(username: str, email: str) -> Tuple[dict, dict]:
    """Helper to register a user and return (user_payload, auth_headers)."""
    register_response = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": "secret123"},
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


def test_match_users_excludes_candidates_with_zero_coverage_even_if_freedom_keywords_overlap(db_session) -> None:
    """Users with coverage_score == 0.0 should be excluded even if their freedom keywords match the team's requirements."""
    creator, creator_headers = register_and_login(
        "freedom_creator", "freedom_creator@example.com"
    )

    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Freedom Circle", "description": "Circle for freedom matching tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    candidate, _ = register_and_login("candidate", "candidate@example.com")

    db_session.add(
        CircleMember(
            user_id=candidate["id"],
            circle_id=circle["id"],
            role=CircleRole.MEMBER,
        )
    )
    db_session.commit()

    # Create a tag definition that candidate does NOT have
    role_tag = TagDefinition(
        circle_id=circle["id"],
        name="role",
        data_type=TagDataType.STRING,
        required=False,
    )
    db_session.add(role_tag)
    db_session.commit()
    db_session.refresh(role_tag)

    # Candidate has NO tags -> coverage_score = 0.0
    # But candidate has freedom keywords that match the team
    _update_circle_member_freedom(
        db_session,
        user_id=candidate["id"],
        circle_id=circle["id"],
        freedom_tag_text="python fastapi ai",
        freedom_tag_profile_json='{"keywords": ["python", "fastapi", "ai"]}',
    )

    # Create team requiring role tag AND freedom keywords
    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Freedom Team",
            "description": "Team with freedom requirements",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["role"],
            "freedom_requirement_text": "looking for python fastapi developers",
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    # Set freedom_requirement_profile_json using helper function
    _update_team_freedom(
        db_session,
        team_id=team["id"],
        freedom_requirement_profile_json='{"keywords": ["python", "fastapi"]}',
    )

    # Ask for candidate users
    match_response = client.get(
        f"/matching/users?team_id={team['id']}",
        headers=creator_headers,
    )
    assert match_response.status_code == 200
    data = match_response.json()

    # Candidate should be excluded despite freedom match because coverage_score == 0.0
    usernames = [item["username"] for item in data]
    assert "candidate" not in usernames


def test_match_users_reranks_candidates_by_freedom_score_when_coverage_equal(db_session) -> None:
    """Among candidates with equal coverage, keyword overlap should rerank by final_score."""
    creator, creator_headers = register_and_login(
        "freedom_rerank_creator", "freedom_rerank_creator@example.com"
    )

    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Freedom Rerank Circle", "description": "Circle for reranking tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    # Register candidates with same coverage but different freedom overlap
    alices, _ = register_and_login("alice_f", "alice_f@example.com")
    bobs, _ = register_and_login("bob_f", "bob_f@example.com")
    carols, _ = register_and_login("carol_f", "carol_f@example.com")

    for member in (alices, bobs, carols):
        db_session.add(
            CircleMember(
                user_id=member["id"],
                circle_id=circle["id"],
                role=CircleRole.MEMBER,
            )
        )
    db_session.commit()

    # Create a tag definition all candidates have
    role_tag = TagDefinition(
        circle_id=circle["id"],
        name="role",
        data_type=TagDataType.STRING,
        required=False,
    )
    db_session.add(role_tag)
    db_session.commit()
    db_session.refresh(role_tag)

    # All candidates have the same required tag (coverage = 1.0)
    for user_id in (alices["id"], bobs["id"], carols["id"]):
        db_session.add(
            UserTag(
                user_id=user_id,
                circle_id=circle["id"],
                tag_definition_id=role_tag.id,
                value="backend",
            )
        )

    # Different freedom keyword overlap
    # Alice: 2/3 keywords match
    _update_circle_member_freedom(
        db_session,
        user_id=alices["id"],
        circle_id=circle["id"],
        freedom_tag_text="python fastapi ai",
        freedom_tag_profile_json='{"keywords": ["python", "fastapi", "ai"]}',
    )
    # Bob: 1/3 keywords match
    _update_circle_member_freedom(
        db_session,
        user_id=bobs["id"],
        circle_id=circle["id"],
        freedom_tag_text="java spring",
        freedom_tag_profile_json='{"keywords": ["java", "spring"]}',
    )
    # Carol: 0/3 keywords match
    _update_circle_member_freedom(
        db_session,
        user_id=carols["id"],
        circle_id=circle["id"],
        freedom_tag_text="ruby rails",
        freedom_tag_profile_json='{"keywords": ["ruby", "rails"]}',
    )

    # Create team requiring role + freedom keywords
    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Freedom Rerank Team",
            "description": "Team with freedom requirements",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["role"],
            "freedom_requirement_text": "looking for python fastapi ai developers",
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    # Set freedom_requirement_profile_json using helper function
    _update_team_freedom(
        db_session,
        team_id=team["id"],
        freedom_requirement_profile_json='{"keywords": ["python", "fastapi", "docker"]}',
    )

    match_response = client.get(
        f"/matching/users?team_id={team['id']}",
        headers=creator_headers,
    )
    assert match_response.status_code == 200
    data = match_response.json()

    # All three should be present (same coverage)
    usernames = [item["username"] for item in data]
    assert "alice_f" in usernames
    assert "bob_f" in usernames
    assert "carol_f" in usernames

    # Order should be by final_score, where keyword overlap participates directly.
    # Alice (2 match) should be first, Bob (0 match) second, Carol (0 match) last.
    assert usernames.index("alice_f") < usernames.index("bob_f")
    assert usernames.index("bob_f") < usernames.index("carol_f")

    alice = next(item for item in data if item["username"] == "alice_f")
    bob = next(item for item in data if item["username"] == "bob_f")

    assert "keyword_overlap_score" in alice
    assert "final_score" in alice
    assert alice["keyword_overlap_score"] > bob["keyword_overlap_score"]
    assert alice["final_score"] > bob["final_score"]


def test_match_users_response_includes_freedom_score_and_matched_keywords(db_session) -> None:
    """The /matching/users endpoint should include overlap and final scoring fields."""
    creator, creator_headers = register_and_login(
        "freedom_fields_creator", "freedom_fields_creator@example.com"
    )

    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Freedom Fields Circle", "description": "Circle for field tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    candidate, _ = register_and_login("fields_candidate", "fields_candidate@example.com")

    db_session.add(
        CircleMember(
            user_id=candidate["id"],
            circle_id=circle["id"],
            role=CircleRole.MEMBER,
        )
    )
    db_session.commit()

    # Create a tag and user value
    role_tag = TagDefinition(
        circle_id=circle["id"],
        name="role",
        data_type=TagDataType.STRING,
        required=False,
    )
    db_session.add(role_tag)
    db_session.commit()
    db_session.refresh(role_tag)

    db_session.add(
        UserTag(
            user_id=candidate["id"],
            circle_id=circle["id"],
            tag_definition_id=role_tag.id,
            value="backend",
        )
    )

    # Set freedom profile on both user and team
    _update_circle_member_freedom(
        db_session,
        user_id=candidate["id"],
        circle_id=circle["id"],
        freedom_tag_text="python fastapi ai",
        freedom_tag_profile_json='{"keywords": ["python", "fastapi", "ai"]}',
    )

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Freedom Fields Team",
            "description": "Team with freedom requirements",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["role"],
            "freedom_requirement_text": "looking for python developers",
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    # Set freedom_requirement_profile_json using helper function
    _update_team_freedom(
        db_session,
        team_id=team["id"],
        freedom_requirement_profile_json='{"keywords": ["python", "fastapi"]}',
    )

    match_response = client.get(
        f"/matching/users?team_id={team['id']}",
        headers=creator_headers,
    )
    assert match_response.status_code == 200
    data = match_response.json()

    # Response should include freedom_score, keyword_overlap_score, final_score,
    # and matched_freedom_keywords for frontend display/debugging.
    assert len(data) == 1
    item = data[0]

    assert "freedom_score" in item
    assert "keyword_overlap_score" in item
    assert "final_score" in item
    assert "matched_freedom_keywords" in item

    # Verify values
    assert item["freedom_score"] > 0.0
    assert item["keyword_overlap_score"] == item["freedom_score"]
    assert item["final_score"] > 0.0
    assert isinstance(item["matched_freedom_keywords"], list)
    # Should match "python" and "fastapi" (2 out of 3 user keywords, or 2/2 team keywords)
    assert "python" in item["matched_freedom_keywords"]
    assert "fastapi" in item["matched_freedom_keywords"]


def test_match_users_freedom_score_computed_from_keyword_overlap(db_session) -> None:
    """Keyword overlap score should be computed from the overlap ratio against team keywords."""
    creator, creator_headers = register_and_login(
        "freedom_score_creator", "freedom_score_creator@example.com"
    )

    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Freedom Score Circle", "description": "Circle for score tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    candidate, _ = register_and_login("score_candidate", "score_candidate@example.com")

    db_session.add(
        CircleMember(
            user_id=candidate["id"],
            circle_id=circle["id"],
            role=CircleRole.MEMBER,
        )
    )
    db_session.commit()

    role_tag = TagDefinition(
        circle_id=circle["id"],
        name="role",
        data_type=TagDataType.STRING,
        required=False,
    )
    db_session.add(role_tag)
    db_session.commit()
    db_session.refresh(role_tag)

    db_session.add(
        UserTag(
            user_id=candidate["id"],
            circle_id=circle["id"],
            tag_definition_id=role_tag.id,
            value="backend",
        )
    )

    # User has 4 keywords, team requires 3
    # 2 keywords overlap -> freedom_score = 2/3 (team coverage) or similar
    _update_circle_member_freedom(
        db_session,
        user_id=candidate["id"],
        circle_id=circle["id"],
        freedom_tag_text="python fastapi docker aws",
        freedom_tag_profile_json='{"keywords": ["python", "fastapi", "docker", "aws"]}',
    )

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Freedom Score Team",
            "description": "Team with specific requirements",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["role"],
            "freedom_requirement_text": "looking for python fastapi docker",
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    # Set freedom_requirement_profile_json using helper function
    _update_team_freedom(
        db_session,
        team_id=team["id"],
        freedom_requirement_profile_json='{"keywords": ["python", "fastapi"]}',
    )

    match_response = client.get(
        f"/matching/users?team_id={team['id']}",
        headers=creator_headers,
    )
    assert match_response.status_code == 200
    data = match_response.json()

    assert len(data) == 1
    item = data[0]

    # User has 4 keywords, 2 overlap with team's 2
    # Expected: matched_keywords = ["python", "fastapi"]
    assert "matched_freedom_keywords" in item
    matched = item["matched_freedom_keywords"]
    assert "python" in matched
    assert "fastapi" in matched
    assert "docker" not in matched
    assert "aws" not in matched

    # freedom_score/keyword_overlap_score should be > 0 and <= 1
    assert 0.0 < item["freedom_score"] <= 1.0
    assert item["keyword_overlap_score"] == item["freedom_score"]
    expected_final = matching_service.compute_final_matching_score(
        coverage=item["coverage_score"],
        jaccard=item["jaccard_score"],
        keyword_overlap=item["keyword_overlap_score"],
    )
    assert item["final_score"] == pytest.approx(expected_final)


def test_match_users_handles_empty_freedom_profiles_gracefully(db_session) -> None:
    """Users or teams without freedom profiles should not cause errors and be treated as having no keywords."""
    creator, creator_headers = register_and_login(
        "freedom_empty_creator", "freedom_empty_creator@example.com"
    )

    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Freedom Empty Circle", "description": "Circle for empty profile tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    candidate, _ = register_and_login("empty_candidate", "empty_candidate@example.com")

    db_session.add(
        CircleMember(
            user_id=candidate["id"],
            circle_id=circle["id"],
            role=CircleRole.MEMBER,
        )
    )
    db_session.commit()

    role_tag = TagDefinition(
        circle_id=circle["id"],
        name="role",
        data_type=TagDataType.STRING,
        required=False,
    )
    db_session.add(role_tag)
    db_session.commit()
    db_session.refresh(role_tag)

    db_session.add(
        UserTag(
            user_id=candidate["id"],
            circle_id=circle["id"],
            tag_definition_id=role_tag.id,
            value="backend",
        )
    )

    # Both user and team have empty freedom profiles
    _update_circle_member_freedom(
        db_session,
        user_id=candidate["id"],
        circle_id=circle["id"],
        freedom_tag_text="",
        freedom_tag_profile_json='{"keywords": []}',
    )

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Freedom Empty Team",
            "description": "Team with empty freedom profile",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["role"],
            "freedom_requirement_text": "",
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    # Set freedom_requirement_profile_json using helper function
    _update_team_freedom(
        db_session,
        team_id=team["id"],
        freedom_requirement_profile_json='{"keywords": []}',
    )

    match_response = client.get(
        f"/matching/users?team_id={team['id']}",
        headers=creator_headers,
    )
    assert match_response.status_code == 200
    data = match_response.json()

    # Candidate should appear
    usernames = [item["username"] for item in data]
    assert "empty_candidate" in usernames

    # Freedom score should be 0 since team has no requirements
    item = data[0]
    assert item["freedom_score"] == 0.0
    assert item["keyword_overlap_score"] == 0.0
    assert item["matched_freedom_keywords"] == []


def test_match_teams_for_user_includes_freedom_score(db_session) -> None:
    """The /matching/teams endpoint should also include overlap and final scoring fields."""
    user, user_headers = register_and_login("freedom_user", "freedom_user@example.com")

    creator, creator_headers = register_and_login(
        "freedom_team_creator", "freedom_team_creator@example.com"
    )

    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Freedom Team Circle", "description": "Circle for team freedom tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(
        CircleMember(user_id=user["id"], circle_id=circle["id"], role=CircleRole.MEMBER)
    )
    db_session.commit()

    role_tag = TagDefinition(
        circle_id=circle["id"],
        name="role",
        data_type=TagDataType.STRING,
        required=False,
    )
    db_session.add(role_tag)
    db_session.commit()
    db_session.refresh(role_tag)

    # User has freedom keywords
    _update_circle_member_freedom(
        db_session,
        user_id=user["id"],
        circle_id=circle["id"],
        freedom_tag_text="python fastapi ai",
        freedom_tag_profile_json='{"keywords": ["python", "fastapi", "ai"]}',
    )

    db_session.add(
        UserTag(
            user_id=user["id"],
            circle_id=circle["id"],
            tag_definition_id=role_tag.id,
            value="backend",
        )
    )
    db_session.commit()

    # Team has freedom requirements
    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Freedom Match Team",
            "description": "Team with freedom requirements",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["role"],
            "freedom_requirement_text": "looking for python fastapi",
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    # Set freedom_requirement_profile_json using helper function
    _update_team_freedom(
        db_session,
        team_id=team["id"],
        freedom_requirement_profile_json='{"keywords": ["python", "fastapi"]}',
    )

    match_response = client.get(
        f"/matching/users?team_id={team['id']}",
        headers=creator_headers,
    )
    assert match_response.status_code == 200
    data = match_response.json()

    # Should include freedom_score and matched_freedom_keywords
    assert len(data) >= 1
    item = data[0]

    assert "freedom_score" in item
    assert "keyword_overlap_score" in item
    assert "final_score" in item
    assert "matched_freedom_keywords" in item

    # Check values
    assert item["freedom_score"] > 0.0
    assert item["keyword_overlap_score"] == item["freedom_score"]
    assert item["final_score"] > 0.0
    assert isinstance(item["matched_freedom_keywords"], list)
    assert "python" in item["matched_freedom_keywords"]
    assert "fastapi" in item["matched_freedom_keywords"]


def test_compute_final_matching_score_uses_weighted_formula() -> None:
    """Final score should use the agreed weighted formula."""
    score = matching_service.compute_final_matching_score(
        coverage=1.0,
        jaccard=0.5,
        keyword_overlap=0.4,
    )

    assert score == pytest.approx(0.84)


def test_matching_helpers_do_not_call_session_get_for_user_tag_name_lookup(db_session, monkeypatch) -> None:
    """Tag-name lookup should use joined queries instead of per-row session.get calls."""
    user, headers = register_and_login("lookup_user", "lookup_user@example.com")
    circle_response = client.post(
        "/circles/",
        headers=headers,
        json={"name": "Lookup Circle", "description": "Circle for helper lookup test"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    role_tag = TagDefinition(
        circle_id=circle["id"],
        name="role",
        data_type=TagDataType.STRING,
        required=False,
    )
    db_session.add(role_tag)
    db_session.commit()
    db_session.refresh(role_tag)
    db_session.add(
        UserTag(
            user_id=user["id"],
            circle_id=circle["id"],
            tag_definition_id=role_tag.id,
            value="backend",
        )
    )
    db_session.commit()

    monkeypatch.setattr(
        db_session,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("session.get should not be used")),
    )

    names = matching_service.get_user_tag_names_for_circle(db_session, user["id"], circle["id"])

    assert names == {"role"}


def test_matching_helpers_do_not_call_session_get_for_user_tag_value_lookup(db_session, monkeypatch) -> None:
    """Tag-value lookup should use joined queries instead of per-row session.get calls."""
    user, headers = register_and_login("value_user", "value_user@example.com")
    circle_response = client.post(
        "/circles/",
        headers=headers,
        json={"name": "Value Lookup Circle", "description": "Circle for helper value lookup"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    role_tag = TagDefinition(
        circle_id=circle["id"],
        name="role",
        data_type=TagDataType.STRING,
        required=False,
    )
    db_session.add(role_tag)
    db_session.commit()
    db_session.refresh(role_tag)
    db_session.add(
        UserTag(
            user_id=user["id"],
            circle_id=circle["id"],
            tag_definition_id=role_tag.id,
            value="backend",
        )
    )
    db_session.commit()

    monkeypatch.setattr(
        db_session,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("session.get should not be used")),
    )

    values = matching_service.get_user_tag_values_for_circle(db_session, user["id"], circle["id"])

    assert values == {"role": "backend"}


def test_decode_freedom_keywords_matches_model_normalization() -> None:
    """Matching helper should reuse model-level freedom profile normalization."""
    keywords = matching_service.decode_freedom_keywords(
        '{"keywords": ["Python", "Python", " fastapi ", "ai", "ml", "ops"]}'
    )

    assert keywords == ["Python", "fastapi", "ai", "ml", "ops"]


def test_match_users_treats_phrase_keyword_with_ascii_token_as_overlap(db_session) -> None:
    """A phrase like 会用AI should still overlap with a team keyword AI."""
    creator, creator_headers = register_and_login(
        "phrase_overlap_creator", "phrase_overlap_creator@example.com"
    )
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Phrase Overlap Circle", "description": "Circle for phrase overlap tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    candidate, _ = register_and_login("phrase_candidate", "phrase_candidate@example.com")
    db_session.add(
        CircleMember(
            user_id=candidate["id"],
            circle_id=circle["id"],
            role=CircleRole.MEMBER,
        )
    )
    db_session.commit()

    role_tag = TagDefinition(
        circle_id=circle["id"],
        name="role",
        data_type=TagDataType.STRING,
        required=False,
    )
    db_session.add(role_tag)
    db_session.commit()
    db_session.refresh(role_tag)
    db_session.add(
        UserTag(
            user_id=candidate["id"],
            circle_id=circle["id"],
            tag_definition_id=role_tag.id,
            value="backend",
        )
    )
    db_session.commit()

    _update_circle_member_freedom(
        db_session,
        user_id=candidate["id"],
        circle_id=circle["id"],
        freedom_tag_text="需要会用AI",
        freedom_tag_profile_json='{"keywords": ["会用AI"]}',
    )

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Phrase Overlap Team",
            "description": "Team requiring AI",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["role"],
            "freedom_requirement_text": "需要AI",
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()
    _update_team_freedom(
        db_session,
        team_id=team["id"],
        freedom_requirement_profile_json='{"keywords": ["AI"]}',
    )

    match_response = client.get(
        f"/matching/users?team_id={team['id']}",
        headers=creator_headers,
    )
    assert match_response.status_code == 200
    data = match_response.json()
    assert len(data) == 1
    assert data[0]["keyword_overlap_score"] > 0.0
    assert "AI" in data[0]["matched_freedom_keywords"]


def test_match_users_treats_ai_tool_phrases_as_overlap(db_session) -> None:
    """Phrases that both embed AI should overlap even when the surrounding Chinese wording differs."""
    creator, creator_headers = register_and_login(
        "ai_tool_phrase_creator", "ai_tool_phrase_creator@example.com"
    )
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "AI Tool Phrase Circle", "description": "Circle for AI tool phrase overlap tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    candidate, _ = register_and_login("ai_tool_phrase_candidate", "ai_tool_phrase_candidate@example.com")
    db_session.add(
        CircleMember(
            user_id=candidate["id"],
            circle_id=circle["id"],
            role=CircleRole.MEMBER,
        )
    )
    db_session.commit()

    role_tag = TagDefinition(
        circle_id=circle["id"],
        name="role",
        data_type=TagDataType.STRING,
        required=False,
    )
    db_session.add(role_tag)
    db_session.commit()
    db_session.refresh(role_tag)
    db_session.add(
        UserTag(
            user_id=candidate["id"],
            circle_id=circle["id"],
            tag_definition_id=role_tag.id,
            value="backend",
        )
    )
    db_session.commit()

    _update_circle_member_freedom(
        db_session,
        user_id=candidate["id"],
        circle_id=circle["id"],
        freedom_tag_text="会用AI工具",
        freedom_tag_profile_json='{"keywords": ["会用AI工具"]}',
    )

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "AI Tool Phrase Team",
            "description": "Team requiring AI tools",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["role"],
            "freedom_requirement_text": "熟练使用AI开发工具",
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()
    _update_team_freedom(
        db_session,
        team_id=team["id"],
        freedom_requirement_profile_json='{"keywords": ["熟练使用AI开发工具"]}',
    )

    match_response = client.get(
        f"/matching/users?team_id={team['id']}",
        headers=creator_headers,
    )
    assert match_response.status_code == 200
    data = match_response.json()
    assert len(data) == 1
    assert data[0]["keyword_overlap_score"] > 0.0
    assert "熟练使用AI开发工具" in data[0]["matched_freedom_keywords"]
