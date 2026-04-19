from src.models.teams import TeamRequirementRule
from src.models.teams import Team, encode_required_tags, encode_required_tag_rules
from src.services.matching import (
    describe_matched_rules,
    get_team_required_tag_names,
    rule_matches_user_value,
)


def test_rule_matches_user_value_matches_integer_inside_closed_range() -> None:
    rule = TeamRequirementRule(
        tag_name="Weekly Hours",
        expected_value={"min": 8, "max": 12},
    )

    assert rule_matches_user_value(rule, 8) is True
    assert rule_matches_user_value(rule, 10) is True
    assert rule_matches_user_value(rule, 12) is True
    assert rule_matches_user_value(rule, 7) is False
    assert rule_matches_user_value(rule, 13) is False


def test_rule_matches_user_value_matches_float_inside_open_ended_range() -> None:
    rule = TeamRequirementRule(
        tag_name="GPA",
        expected_value={"min": None, "max": 3.8},
    )

    assert rule_matches_user_value(rule, 3.8) is True
    assert rule_matches_user_value(rule, 3.5) is True
    assert rule_matches_user_value(rule, 4.0) is False


def test_rule_matches_user_value_keeps_legacy_scalar_numeric_rule_behavior() -> None:
    rule = TeamRequirementRule(tag_name="Weekly Hours", expected_value=10)

    assert rule_matches_user_value(rule, 10) is True
    assert rule_matches_user_value(rule, 12) is False


def test_describe_matched_rules_uses_actual_numeric_value_for_range_rule() -> None:
    rules = [
        TeamRequirementRule(
            tag_name="Budget Level",
            expected_value={"min": 1, "max": 3},
        )
    ]

    matched = describe_matched_rules(rules, {"Budget Level": 2})

    assert matched == ["Budget Level=2"]


def test_get_team_required_tag_names_unions_presence_only_and_structured_rules() -> None:
    team = Team(
        name="Core Team",
        circle_id=1,
        creator_id=1,
        max_members=4,
        required_tags_json=encode_required_tags(["Preferred Role", "Focus Track"]),
        required_tag_rules_json=encode_required_tag_rules(
            [
                TeamRequirementRule(
                    tag_name="Weekly Hours",
                    expected_value={"min": 8, "max": 12},
                )
            ]
        ),
    )

    assert get_team_required_tag_names(team) == {
        "Preferred Role",
        "Focus Track",
        "Weekly Hours",
    }
