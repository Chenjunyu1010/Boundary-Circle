from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

from sqlmodel import Session, select

from src.db.database import create_db_and_tables, engine
from src.models.core import Circle, User, UserCreate
from src.models.profile import UserProfile
from src.models.tags import CircleMember, CircleRole, TagDataType, TagDefinition, UserTag
from src.models.teams import (
    Invitation,
    InvitationKind,
    InvitationStatus,
    Team,
    TeamMember,
    TeamRequirementRule,
    TeamStatus,
    encode_freedom_profile,
    encode_required_tag_rules,
    encode_required_tags,
)
from src.services.users import create_user_account


PASSWORD = "SeedData123!"


@dataclass(frozen=True)
class TagSeed:
    name: str
    data_type: TagDataType
    required: bool = False
    options: Optional[List[str]] = None
    max_selections: Optional[int] = None
    description: Optional[str] = None


@dataclass(frozen=True)
class TeamSeed:
    slug: str
    name: str
    description: str
    creator: str
    max_members: int
    members: List[str]
    required_tags: List[str]
    required_tag_rules: List[TeamRequirementRule]
    freedom_text: Optional[str] = None
    freedom_keywords: Optional[List[str]] = None


@dataclass(frozen=True)
class InvitationSeed:
    team_slug: str
    inviter: str
    invitee: str
    status: InvitationStatus
    kind: InvitationKind = InvitationKind.INVITE


@dataclass(frozen=True)
class CircleSeed:
    slug: str
    name: str
    description: str
    category: str
    creator: str
    members: List[str]
    tags: List[TagSeed]
    user_tags: Dict[str, Dict[str, Any]]
    teams: List[TeamSeed]
    invitations: List[InvitationSeed]
    freedom_source_tags: Optional[Dict[str, Dict[str, Any]]] = None
    member_freedom_profiles: Optional[Dict[str, tuple[str, dict[str, list[str]]]]] = None


@dataclass(frozen=True)
class ArchetypeSeed:
    major: str
    preferred_role: str
    tech_stack: List[str]
    weekly_hours: int
    open_to_lead: bool
    focus_track: str
    freedom_text: str
    freedom_keywords: List[str]


@dataclass(frozen=True)
class DatasetSeed:
    users: Dict[str, "UserSeed"]
    circles: List[CircleSeed]


@dataclass(frozen=True)
class UserSeed:
    full_name: str
    gender: str
    birthday: str
    bio: str
    show_full_name: bool = True
    show_gender: bool = True
    show_birthday: bool = True
    show_email: bool = True
    show_bio: bool = True


@dataclass
class SeedSummary:
    users: int = 0
    circles: int = 0
    tags: int = 0
    user_tags: int = 0
    teams: int = 0
    team_members: int = 0
    invitations: int = 0


def dataset_user_prefix(dataset: str) -> str:
    return f"seed_{dataset}_"


def dataset_circle_prefix(dataset: str) -> str:
    return f"[SEED {dataset.upper()}] "


def dataset_team_prefix(dataset: str) -> str:
    return f"[SEED {dataset.upper()}] "


def seed_username(dataset: str, slug: str) -> str:
    return f"{dataset_user_prefix(dataset)}{slug}"


def seed_email(dataset: str, slug: str) -> str:
    return f"{seed_username(dataset, slug)}@example.test"


def seed_circle_name(dataset: str, name: str) -> str:
    return f"{dataset_circle_prefix(dataset)}{name}"


def seed_team_name(dataset: str, name: str) -> str:
    return f"{dataset_team_prefix(dataset)}{name}"


def _options(options: Optional[List[str]]) -> Optional[str]:
    if options is None:
        return None
    return json.dumps(options)


def _normalize_tag_value(value: Any) -> str:
    if isinstance(value, list):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _add_keyword(target: list[str], keyword: str) -> None:
    normalized = keyword.strip().lower()
    if normalized and normalized not in target:
        target.append(normalized)


def _keywords_from_value(value: Any) -> list[str]:
    keywords: list[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                _add_keyword(keywords, item)
        return keywords
    if isinstance(value, bool):
        if value:
            _add_keyword(keywords, "collaboration")
        return keywords
    if isinstance(value, (int, float)):
        return keywords
    if isinstance(value, str):
        _add_keyword(keywords, value)
    return keywords


def build_member_freedom_profile(values: Dict[str, Any], bio: str) -> tuple[str, dict[str, list[str]]]:
    keywords: list[str] = []
    sentences: list[str] = []

    preferred_role = values.get("Preferred Role") or values.get("Build Role")
    if isinstance(preferred_role, str) and preferred_role.strip():
        sentences.append(f"Prefers {preferred_role.lower()} work")
        _add_keyword(keywords, preferred_role)

    major = values.get("Major")
    if isinstance(major, str) and major.strip():
        sentences.append(f"Studies {major}")
        _add_keyword(keywords, major)

    focus_track = values.get("Focus Track") or values.get("Track")
    if isinstance(focus_track, str) and focus_track.strip():
        sentences.append(f"Interested in {focus_track.lower()}")
        _add_keyword(keywords, focus_track)

    for tech_keyword in _keywords_from_value(values.get("Tech Stack") or values.get("Toolkit") or []):
        _add_keyword(keywords, tech_keyword)
    if values.get("Wants Research") is True:
        _add_keyword(keywords, "research")
        sentences.append("Enjoys research work")
    if values.get("Open To Lead") is True:
        _add_keyword(keywords, "leadership")
        sentences.append("Open to leading coordination")

    if not keywords:
        _add_keyword(keywords, "collaboration")
    if not sentences:
        sentences.append(bio)

    return ". ".join(sentences), {"keywords": keywords[:5]}


def build_team_freedom_profile(team_seed: TeamSeed, creator_values: Dict[str, Any]) -> tuple[str, dict[str, list[str]]]:
    keywords: list[str] = []

    for rule in team_seed.required_tag_rules:
        expected_value = rule.expected_value
        if isinstance(expected_value, list):
            for item in expected_value:
                _add_keyword(keywords, str(item))
        else:
            _add_keyword(keywords, str(expected_value))

    if team_seed.required_tags:
        for tag_name in team_seed.required_tags:
            for keyword in _keywords_from_value(creator_values.get(tag_name)):
                _add_keyword(keywords, keyword)

    if not keywords:
        for fallback_key in ("Preferred Role", "Build Role", "Tech Stack", "Toolkit", "Focus Track", "Track"):
            for keyword in _keywords_from_value(creator_values.get(fallback_key)):
                _add_keyword(keywords, keyword)
            if len(keywords) >= 5:
                break

    if not keywords:
        _add_keyword(keywords, "collaboration")

    text = f"{team_seed.description} Looking for teammates with {', '.join(keywords[:3])}."
    return text, {"keywords": keywords[:5]}


def build_demo_dataset() -> DatasetSeed:
    users = {
        "alice": UserSeed("Alice Chen", "Female", "2002-03-14", "Research-driven builder who enjoys structuring AI demos."),
        "ben": UserSeed("Ben Li", "Male", "2001-11-02", "Backend teammate focused on reliable APIs and data flow."),
        "clara": UserSeed("Clara Wu", "Female", "2003-05-27", "Frontend-heavy collaborator who likes clear product stories."),
        "derek": UserSeed("Derek Sun", "Male", "2002-08-09", "Comfortable with Python systems and technical iteration."),
        "eva": UserSeed("Eva Lin", "Female", "2002-12-18", "Enjoys coordination, demos, and keeping team scope realistic."),
        "felix": UserSeed("Felix Zhou", "Male", "2001-07-30", "Hackathon-oriented builder who moves quickly from idea to MVP."),
        "grace": UserSeed("Grace Fang", "Female", "2003-01-16", "Design-leaning teammate focused on presentation and clarity."),
    }
    circles = [
        CircleSeed(
            slug="ai_capstone",
            name="AI Capstone Showcase",
            description="Demo-ready circle for capstone matching.",
            category="Course",
            creator="alice",
            members=["alice", "ben", "clara", "derek", "eva"],
            tags=[
                TagSeed("Major", TagDataType.SINGLE_SELECT, required=True, options=["AI", "SE", "DS"]),
                TagSeed("Preferred Role", TagDataType.SINGLE_SELECT, required=True, options=["Frontend", "Backend", "Research", "PM"]),
                TagSeed("Tech Stack", TagDataType.MULTI_SELECT, options=["Python", "React", "SQL", "PyTorch"], max_selections=3),
                TagSeed("Weekly Hours", TagDataType.INTEGER),
                TagSeed("Wants Research", TagDataType.BOOLEAN),
            ],
            user_tags={
                "alice": {"Major": "AI", "Preferred Role": "Research", "Tech Stack": ["Python", "PyTorch"], "Weekly Hours": 12, "Wants Research": True},
                "ben": {"Major": "SE", "Preferred Role": "Backend", "Tech Stack": ["Python", "SQL"], "Weekly Hours": 10, "Wants Research": False},
                "clara": {"Major": "DS", "Preferred Role": "Frontend", "Tech Stack": ["React", "Python"], "Weekly Hours": 8, "Wants Research": False},
                "derek": {"Major": "AI", "Preferred Role": "Backend", "Tech Stack": ["Python", "SQL"], "Weekly Hours": 9, "Wants Research": True},
                "eva": {"Major": "SE", "Preferred Role": "PM", "Tech Stack": ["React"], "Weekly Hours": 6, "Wants Research": False},
            },
            teams=[
                TeamSeed(
                    slug="vision_builders",
                    name="Vision Builders",
                    description="Computer vision capstone team.",
                    creator="alice",
                    max_members=4,
                    members=["alice", "ben"],
                    required_tags=[],
                    required_tag_rules=[
                        TeamRequirementRule(tag_name="Major", expected_value="AI"),
                        TeamRequirementRule(tag_name="Tech Stack", expected_value=["Python", "PyTorch"]),
                    ],
                ),
                TeamSeed(
                    slug="data_bridge",
                    name="Data Bridge",
                    description="Data platform and model serving.",
                    creator="clara",
                    max_members=3,
                    members=["clara"],
                    required_tags=["Preferred Role", "Tech Stack"],
                    required_tag_rules=[],
                ),
            ],
            invitations=[
                InvitationSeed("vision_builders", "alice", "derek", InvitationStatus.PENDING),
                InvitationSeed("vision_builders", "ben", "clara", InvitationStatus.REJECTED),
                InvitationSeed("data_bridge", "clara", "eva", InvitationStatus.ACCEPTED),
                InvitationSeed(
                    "vision_builders",
                    "eva",
                    "alice",
                    InvitationStatus.PENDING,
                    kind=InvitationKind.JOIN_REQUEST,
                ),
            ],
        ),
        CircleSeed(
            slug="hack_weekend",
            name="Hack Weekend",
            description="Short-form hackathon style demo circle.",
            category="Event",
            creator="felix",
            members=["felix", "grace", "alice", "eva"],
            tags=[
                TagSeed("Track", TagDataType.SINGLE_SELECT, required=True, options=["AI Agent", "Campus Tooling", "Social Good"]),
                TagSeed("Build Role", TagDataType.SINGLE_SELECT, options=["Engineer", "Designer", "Pitch"]),
                TagSeed("Toolkit", TagDataType.MULTI_SELECT, options=["Next.js", "FastAPI", "SQLite", "Figma"], max_selections=3),
                TagSeed("Weekend Hours", TagDataType.INTEGER),
            ],
            user_tags={
                "felix": {"Track": "AI Agent", "Build Role": "Engineer", "Toolkit": ["FastAPI", "SQLite"], "Weekend Hours": 14},
                "grace": {"Track": "Social Good", "Build Role": "Designer", "Toolkit": ["Figma"], "Weekend Hours": 9},
                "alice": {"Track": "AI Agent", "Build Role": "Pitch", "Toolkit": ["Next.js", "FastAPI"], "Weekend Hours": 7},
                "eva": {"Track": "Campus Tooling", "Build Role": "Engineer", "Toolkit": ["Next.js", "SQLite"], "Weekend Hours": 10},
            },
            teams=[
                TeamSeed(
                    slug="campus_loop",
                    name="Campus Loop",
                    description="Hackathon MVP for campus workflows.",
                    creator="felix",
                    max_members=4,
                    members=["felix", "eva"],
                    required_tags=[],
                    required_tag_rules=[
                        TeamRequirementRule(tag_name="Track", expected_value="Campus Tooling"),
                    ],
                ),
                TeamSeed(
                    slug="kindred_signal",
                    name="Kindred Signal",
                    description="Pitch-led community project.",
                    creator="grace",
                    max_members=3,
                    members=["grace"],
                    required_tags=["Build Role"],
                    required_tag_rules=[],
                ),
            ],
            invitations=[
                InvitationSeed("campus_loop", "felix", "alice", InvitationStatus.ACCEPTED),
                InvitationSeed("kindred_signal", "grace", "eva", InvitationStatus.PENDING),
            ],
        ),
    ]
    return DatasetSeed(users=users, circles=circles)


def build_stress_dataset() -> DatasetSeed:
    user_names = {
        "amir": "Amir He",
        "bella": "Bella Xu",
        "cyrus": "Cyrus Gu",
        "diana": "Diana Qiu",
        "ethan": "Ethan Luo",
        "flora": "Flora Yin",
        "gavin": "Gavin Hu",
        "hazel": "Hazel Tang",
        "isaac": "Isaac Fan",
        "julia": "Julia Xie",
        "kevin": "Kevin Rao",
        "luna": "Luna Gao",
        "mason": "Mason Ji",
        "nora": "Nora Peng",
        "owen": "Owen Yue",
        "pearl": "Pearl Yang",
        "quentin": "Quentin Shen",
        "rachel": "Rachel Nie",
    }
    genders = ["Male", "Female", "Other", "Prefer not to say"]
    users = {
        slug: UserSeed(
            full_name=full_name,
            gender=genders[index % len(genders)],
            birthday=f"200{index % 4 + 1}-{index % 9 + 1:02d}-{index % 17 + 10:02d}",
            bio=f"{full_name} contributes steadily across course and project collaborations.",
            show_birthday=index % 3 != 0,
            show_email=index % 4 != 0,
        )
        for index, (slug, full_name) in enumerate(user_names.items())
    }
    majors = ["AI", "SE", "DS", "HCI"]
    roles = ["Frontend", "Backend", "Research", "PM"]
    stacks = [
        ["Python", "SQL"],
        ["React", "TypeScript"],
        ["Python", "PyTorch"],
        ["React", "Figma"],
        ["FastAPI", "SQLite"],
        ["Python", "Docker"],
    ]
    user_order = list(users)

    circle_specs = [
        ("systems_lab", "Systems Lab", "Course", user_order[:8]),
        ("product_studio", "Product Studio", "Course", user_order[4:13]),
        ("research_exchange", "Research Exchange", "Interest", user_order[8:16]),
        ("community_build", "Community Build", "Event", user_order[2:18:2]),
    ]
    circles: List[CircleSeed] = []
    for index, (slug, name, category, members) in enumerate(circle_specs):
        user_tags: Dict[str, Dict[str, Any]] = {}
        base_user_tags: Dict[str, Dict[str, Any]] = {}
        for offset, member in enumerate(members):
            user_index = user_order.index(member)
            base_values = {
                "Major": majors[(user_index + index) % len(majors)],
                "Preferred Role": roles[(user_index + index) % len(roles)],
                "Tech Stack": stacks[(user_index + offset) % len(stacks)],
                "Weekly Hours": 6 + ((user_index + index) % 10),
                "Open To Lead": (user_index + index) % 2 == 0,
                "Focus Track": ["AI Infra", "Campus Ops", "Data Viz", "Community"][((user_index // 2) + index) % 4],
            }
            values = dict(base_values)
            if (user_index + index) % 3 == 0:
                values.pop("Open To Lead")
            if (user_index + index) % 4 == 0:
                values.pop("Focus Track")
            if (user_index + index) % 5 == 0:
                values.pop("Weekly Hours")
            if (user_index + index) % 6 == 0:
                values.pop("Tech Stack")
            if (user_index + index) % 7 == 0:
                values.pop("Preferred Role")
            base_user_tags[member] = base_values
            user_tags[member] = values

        teams = [
            TeamSeed(
                slug=f"{slug}_alpha",
                name=f"{name} Alpha",
                description=f"{name} core delivery team.",
                creator=members[0],
                max_members=4,
                members=members[: min(3, len(members))],
                required_tags=["Preferred Role", "Tech Stack"] if index % 2 == 0 else [],
                required_tag_rules=[] if index % 2 == 0 else [
                    TeamRequirementRule(
                        tag_name="Focus Track",
                        expected_value=base_user_tags[members[0]]["Focus Track"],
                    ),
                    TeamRequirementRule(
                        tag_name="Tech Stack",
                        expected_value=base_user_tags[members[1]]["Tech Stack"],
                    ),
                ],
            ),
            TeamSeed(
                slug=f"{slug}_beta",
                name=f"{name} Beta",
                description=f"{name} exploratory team.",
                creator=members[2],
                max_members=5,
                members=members[2:5],
                required_tags=[],
                required_tag_rules=[
                    TeamRequirementRule(
                        tag_name="Major",
                        expected_value=base_user_tags[members[2]]["Major"],
                    ),
                ],
            ),
        ]
        if index < 2:
            teams.append(
                TeamSeed(
                    slug=f"{slug}_gamma",
                    name=f"{name} Gamma",
                    description=f"{name} overflow team.",
                    creator=members[-2],
                    max_members=3,
                    members=members[-2:],
                    required_tags=["Major"],
                    required_tag_rules=[],
                )
            )

        invitations = [
            InvitationSeed(teams[0].slug, teams[0].creator, members[-1], InvitationStatus.PENDING),
            InvitationSeed(teams[1].slug, teams[1].creator, members[1], InvitationStatus.REJECTED),
            InvitationSeed(teams[1].slug, teams[1].creator, members[-2], InvitationStatus.ACCEPTED),
        ]
        if len(members) >= 6:
            invitations.append(
                InvitationSeed(
                    teams[0].slug,
                    members[-2],
                    teams[0].creator,
                    InvitationStatus.PENDING,
                    kind=InvitationKind.JOIN_REQUEST,
                )
            )

        circles.append(
            CircleSeed(
                slug=slug,
                name=name,
                description=f"Stress dataset circle for {name}.",
                category=category,
                creator=members[0],
                members=members,
                tags=[
                    TagSeed("Major", TagDataType.SINGLE_SELECT, required=True, options=majors),
                    TagSeed("Preferred Role", TagDataType.SINGLE_SELECT, options=roles),
                    TagSeed("Tech Stack", TagDataType.MULTI_SELECT, options=sorted({item for stack in stacks for item in stack}), max_selections=3),
                    TagSeed("Weekly Hours", TagDataType.INTEGER),
                    TagSeed("Open To Lead", TagDataType.BOOLEAN),
                    TagSeed("Focus Track", TagDataType.SINGLE_SELECT, options=["AI Infra", "Campus Ops", "Data Viz", "Community"]),
                ],
                user_tags=user_tags,
                freedom_source_tags=base_user_tags,
                teams=teams,
                invitations=invitations,
            )
        )
    return DatasetSeed(users=users, circles=circles)


def build_stress2_dataset() -> DatasetSeed:
    user_names = {
        "amir": "Amir He",
        "bella": "Bella Xu",
        "cyrus": "Cyrus Gu",
        "diana": "Diana Qiu",
        "ethan": "Ethan Luo",
        "flora": "Flora Yin",
        "gavin": "Gavin Hu",
        "hazel": "Hazel Tang",
        "isaac": "Isaac Fan",
        "julia": "Julia Xie",
        "kevin": "Kevin Rao",
        "luna": "Luna Gao",
        "mason": "Mason Ji",
        "nora": "Nora Peng",
        "owen": "Owen Yue",
        "pearl": "Pearl Yang",
        "quentin": "Quentin Shen",
        "rachel": "Rachel Nie",
        "sam": "Sam Wu",
        "tina": "Tina Sun",
        "uma": "Uma Zhen",
        "vincent": "Vincent Liu",
        "wendy": "Wendy Ma",
        "xavier": "Xavier Ren",
        "yara": "Yara Bao",
        "zane": "Zane Fu",
        "amber": "Amber Mo",
        "blake": "Blake Du",
        "celine": "Celine Shao",
        "damon": "Damon Cheng",
        "elsa": "Elsa Yao",
        "fiona": "Fiona Lai",
        "harry": "Harry Zhou",
        "iris": "Iris Deng",
        "jonah": "Jonah Qi",
        "kira": "Kira Song",
    }
    genders = ["Male", "Female", "Other", "Prefer not to say"]
    users = {
        slug: UserSeed(
            full_name=full_name,
            gender=genders[index % len(genders)],
            birthday=f"200{index % 5}-{(index % 11) + 1:02d}-{(index % 19) + 8:02d}",
            bio=f"{full_name} is part of the stress2 showcase seed and participates in cross-functional collaborations.",
            show_birthday=index % 4 != 0,
            show_email=index % 5 != 0,
            show_bio=True,
        )
        for index, (slug, full_name) in enumerate(user_names.items(), start=1)
    }

    archetypes = [
        ArchetypeSeed(
            major="AI",
            preferred_role="Backend",
            tech_stack=["Python", "FastAPI", "Docker"],
            weekly_hours=12,
            open_to_lead=True,
            focus_track="AI Infra",
            freedom_text="喜欢用AI开发工具做自动化，熟悉Python、FastAPI和Docker，能推进后端落地。",
            freedom_keywords=["AI开发工具", "Python", "FastAPI", "Docker", "自动化"],
        ),
        ArchetypeSeed(
            major="HCI",
            preferred_role="Design",
            tech_stack=["Figma", "React", "TypeScript"],
            weekly_hours=9,
            open_to_lead=False,
            focus_track="Agent UX",
            freedom_text="擅长把AI能力做成可用界面，关注Agent UX、Figma原型和前端体验。",
            freedom_keywords=["AI产品", "Agent UX", "Figma", "React", "前端体验"],
        ),
        ArchetypeSeed(
            major="DS",
            preferred_role="Data",
            tech_stack=["Python", "SQL", "Docker"],
            weekly_hours=11,
            open_to_lead=False,
            focus_track="Data Viz",
            freedom_text="偏好数据清洗、SQL分析和可视化，也会用AI辅助做数据工作流。",
            freedom_keywords=["数据分析", "SQL", "可视化", "AI工作流", "Python"],
        ),
        ArchetypeSeed(
            major="AI",
            preferred_role="Research",
            tech_stack=["Python", "PyTorch", "SQL"],
            weekly_hours=13,
            open_to_lead=True,
            focus_track="Research Ops",
            freedom_text="喜欢做模型评估、prompt实验和研究复现，能写清楚实验结论。",
            freedom_keywords=["模型评估", "Prompt", "研究复现", "PyTorch", "实验结论"],
        ),
        ArchetypeSeed(
            major="SE",
            preferred_role="Frontend",
            tech_stack=["React", "TypeScript", "Next.js"],
            weekly_hours=10,
            open_to_lead=False,
            focus_track="Creator Tools",
            freedom_text="喜欢做产品界面和前端交互，能把AI辅助能力接进Web工作流。",
            freedom_keywords=["前端", "React", "TypeScript", "AI辅助", "Web工作流"],
        ),
        ArchetypeSeed(
            major="Biz",
            preferred_role="PM",
            tech_stack=["SQL", "Figma", "Notion"],
            weekly_hours=8,
            open_to_lead=True,
            focus_track="Campus Ops",
            freedom_text="偏项目管理和流程推进，适合梳理需求、拆任务，也会用AI做资料整理。",
            freedom_keywords=["项目管理", "需求拆解", "AI整理", "流程推进", "协作"],
        ),
        ArchetypeSeed(
            major="SE",
            preferred_role="Backend",
            tech_stack=["Go", "SQL", "Docker"],
            weekly_hours=11,
            open_to_lead=True,
            focus_track="Health Tech",
            freedom_text="偏系统实现和服务稳定性，熟悉Go、SQL、Docker，也会用AI辅助排查问题。",
            freedom_keywords=["Go", "SQL", "Docker", "服务稳定性", "AI辅助"],
        ),
        ArchetypeSeed(
            major="HCI",
            preferred_role="PM",
            tech_stack=["Figma", "React", "Next.js"],
            weekly_hours=7,
            open_to_lead=False,
            focus_track="Community",
            freedom_text="喜欢社区类产品和内容运营，希望做有明确用户反馈的AI功能。",
            freedom_keywords=["社区产品", "内容运营", "AI功能", "用户反馈", "Figma"],
        ),
    ]

    all_stack_options = sorted(
        {
            item
            for archetype in archetypes
            for item in archetype.tech_stack
        }
    )
    majors = sorted({archetype.major for archetype in archetypes})
    roles = sorted({archetype.preferred_role for archetype in archetypes})
    tracks = sorted({archetype.focus_track for archetype in archetypes})

    user_order = list(users)
    base_user_tags: Dict[str, Dict[str, Any]] = {}
    member_freedom_profiles: Dict[str, tuple[str, dict[str, list[str]]]] = {}
    for index, slug in enumerate(user_order):
        archetype = archetypes[index % len(archetypes)]
        base_user_tags[slug] = {
            "Major": archetype.major,
            "Preferred Role": archetype.preferred_role,
            "Tech Stack": archetype.tech_stack,
            "Weekly Hours": archetype.weekly_hours,
            "Open To Lead": archetype.open_to_lead,
            "Focus Track": archetype.focus_track,
        }
        member_freedom_profiles[slug] = (
            archetype.freedom_text,
            {"keywords": archetype.freedom_keywords[:5]},
        )

    circle_specs = [
        ("ai_factory", "AI Factory", "Course", user_order[0:10]),
        ("product_garage", "Product Garage", "Course", user_order[4:16]),
        ("design_signal", "Design Signal", "Interest", user_order[8:20]),
        ("research_exchange", "Research Exchange", "Course", user_order[12:24]),
        ("community_lab", "Community Lab", "Event", user_order[16:28]),
        ("delivery_hub", "Delivery Hub", "Project", user_order[20:36]),
    ]

    circles: List[CircleSeed] = []
    for index, (slug, name, category, members) in enumerate(circle_specs):
        circle_user_tags: Dict[str, Dict[str, Any]] = {}
        circle_member_freedom: Dict[str, tuple[str, dict[str, list[str]]]] = {}
        for offset, member in enumerate(members):
            values = dict(base_user_tags[member])
            # Keep some sparsity so the frontend and matching pages show varied completeness.
            if (index + offset) % 4 == 0:
                values.pop("Open To Lead", None)
            if (index + offset) % 5 == 0:
                values.pop("Weekly Hours", None)
            if (index + offset) % 6 == 0:
                values.pop("Focus Track", None)
            if (index + offset) % 7 == 0:
                values.pop("Tech Stack", None)
            circle_user_tags[member] = values
            circle_member_freedom[member] = member_freedom_profiles[member]

        teams = [
            TeamSeed(
                slug=f"{slug}_ai_core",
                name=f"{name} AI Core",
                description=f"{name} core team focused on delivering production-ready AI features.",
                creator=members[0],
                max_members=4,
                members=members[:3],
                required_tags=["Preferred Role", "Tech Stack"],
                required_tag_rules=[],
                freedom_text="熟练使用AI开发工具，最好能做后端集成、自动化或评测落地。",
                freedom_keywords=["AI开发工具", "后端", "自动化", "评测", "集成"],
            ),
            TeamSeed(
                slug=f"{slug}_design_ops",
                name=f"{name} Design Ops",
                description=f"{name} team for UX, prototype polish, and communication-heavy delivery.",
                creator=members[2],
                max_members=5,
                members=members[2:5],
                required_tags=[],
                required_tag_rules=[
                    TeamRequirementRule(tag_name="Preferred Role", expected_value="Design"),
                    TeamRequirementRule(tag_name="Focus Track", expected_value=base_user_tags[members[2]]["Focus Track"]),
                ],
                freedom_text="希望队友能把AI能力转成清晰体验，擅长Figma、前端协作或用户访谈。",
                freedom_keywords=["AI体验", "Figma", "前端协作", "用户访谈", "设计"],
            ),
        ]

        if len(members) >= 8:
            teams.append(
                TeamSeed(
                    slug=f"{slug}_data_loop",
                    name=f"{name} Data Loop",
                    description=f"{name} team for analytics, data workflows, and operational reporting.",
                    creator=members[-3],
                    max_members=4,
                    members=members[-3:],
                    required_tags=[],
                    required_tag_rules=[
                        TeamRequirementRule(tag_name="Major", expected_value="DS"),
                    ],
                    freedom_text="需要会做数据分析、SQL和报表，也欢迎会用AI辅助清洗数据的同学。",
                    freedom_keywords=["数据分析", "SQL", "报表", "AI辅助", "数据清洗"],
                )
            )

        invitations = [
            InvitationSeed(teams[0].slug, teams[0].creator, members[-1], InvitationStatus.PENDING),
            InvitationSeed(teams[0].slug, teams[0].creator, members[-2], InvitationStatus.REJECTED),
            InvitationSeed(teams[1].slug, teams[1].creator, members[1], InvitationStatus.ACCEPTED),
            InvitationSeed(
                teams[1].slug,
                members[-1],
                teams[1].creator,
                InvitationStatus.PENDING,
                kind=InvitationKind.JOIN_REQUEST,
            ),
        ]
        if len(teams) > 2:
            invitations.append(
                InvitationSeed(teams[2].slug, teams[2].creator, members[0], InvitationStatus.ACCEPTED)
            )

        circles.append(
            CircleSeed(
                slug=slug,
                name=name,
                description=f"Stress2 dataset circle for {name}.",
                category=category,
                creator=members[0],
                members=members,
                tags=[
                    TagSeed("Major", TagDataType.SINGLE_SELECT, required=True, options=majors),
                    TagSeed("Preferred Role", TagDataType.SINGLE_SELECT, options=roles),
                    TagSeed("Tech Stack", TagDataType.MULTI_SELECT, options=all_stack_options, max_selections=3),
                    TagSeed("Weekly Hours", TagDataType.INTEGER),
                    TagSeed("Open To Lead", TagDataType.BOOLEAN),
                    TagSeed("Focus Track", TagDataType.SINGLE_SELECT, options=tracks),
                ],
                user_tags=circle_user_tags,
                teams=teams,
                invitations=invitations,
                freedom_source_tags=base_user_tags,
                member_freedom_profiles=circle_member_freedom,
            )
        )

    return DatasetSeed(users=users, circles=circles)


def get_dataset_blueprint(dataset: str) -> DatasetSeed:
    if dataset == "demo":
        return build_demo_dataset()
    if dataset == "stress":
        return build_stress_dataset()
    if dataset == "stress2":
        return build_stress2_dataset()
    raise ValueError(f"Unsupported dataset: {dataset}")


def _user_matches_dataset(user: User, dataset: str) -> bool:
    return user.username.startswith(dataset_user_prefix(dataset))


def _circle_matches_dataset(circle: Circle, dataset: str) -> bool:
    return circle.name.startswith(dataset_circle_prefix(dataset))


def _team_matches_dataset(team: Team, dataset: str) -> bool:
    return team.name.startswith(dataset_team_prefix(dataset))


def _filter_by_dataset(items: Iterable[Any], predicate: Callable[[Any], bool]) -> List[Any]:
    return [item for item in items if predicate(item)]


def reset_dataset(session: Session, dataset: str) -> SeedSummary:
    users = _filter_by_dataset(session.exec(select(User)).all(), lambda item: _user_matches_dataset(item, dataset))
    circles = _filter_by_dataset(session.exec(select(Circle)).all(), lambda item: _circle_matches_dataset(item, dataset))
    user_ids: Set[int] = {user.id for user in users if user.id is not None}
    circle_ids: Set[int] = {circle.id for circle in circles if circle.id is not None}
    profiles = [
        profile
        for profile in session.exec(select(UserProfile)).all()
        if profile.user_id in user_ids
    ]

    teams = _filter_by_dataset(
        session.exec(select(Team)).all(),
        lambda item: _team_matches_dataset(item, dataset) or item.circle_id in circle_ids,
    )
    team_ids: Set[int] = {team.id for team in teams if team.id is not None}

    invitations = [
        invitation
        for invitation in session.exec(select(Invitation)).all()
        if invitation.team_id in team_ids
        or invitation.inviter_id in user_ids
        or invitation.invitee_id in user_ids
    ]
    team_members = [
        membership
        for membership in session.exec(select(TeamMember)).all()
        if membership.team_id in team_ids or membership.user_id in user_ids
    ]
    user_tags = [
        user_tag
        for user_tag in session.exec(select(UserTag)).all()
        if user_tag.circle_id in circle_ids or user_tag.user_id in user_ids
    ]
    tag_definitions = [
        tag
        for tag in session.exec(select(TagDefinition)).all()
        if tag.circle_id in circle_ids
    ]
    circle_members = [
        membership
        for membership in session.exec(select(CircleMember)).all()
        if membership.circle_id in circle_ids or membership.user_id in user_ids
    ]

    summary = SeedSummary(
        users=len(users),
        circles=len(circles),
        tags=len(tag_definitions),
        user_tags=len(user_tags),
        teams=len(teams),
        team_members=len(team_members),
        invitations=len(invitations),
    )

    for invitation in invitations:
        session.delete(invitation)
    for membership in team_members:
        session.delete(membership)
    for team in teams:
        session.delete(team)
    for user_tag in user_tags:
        session.delete(user_tag)
    for tag_definition in tag_definitions:
        session.delete(tag_definition)
    for membership in circle_members:
        session.delete(membership)
    for circle in circles:
        session.delete(circle)
    for profile in profiles:
        session.delete(profile)
    for user in users:
        session.delete(user)
    session.commit()
    return summary


def _get_user_id(session: Session, username: str) -> int:
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None or user.id is None:
        raise ValueError(f"User not found for seed username: {username}")
    return user.id


def seed_dataset(session: Session, dataset: str) -> SeedSummary:
    blueprint = get_dataset_blueprint(dataset)
    reset_dataset(session, dataset)

    summary = SeedSummary()
    usernames: Dict[str, str] = {}
    for slug, user_seed in blueprint.users.items():
        username = seed_username(dataset, slug)
        created_user = create_user_account(
            session,
            UserCreate(
                username=username,
                email=seed_email(dataset, slug),
                full_name=user_seed.full_name,
                password=PASSWORD,
            ),
        )
        if created_user.id is None:
            raise ValueError(f"User ID missing for seed user: {username}")
        session.add(
            UserProfile(
                user_id=created_user.id,
                gender=user_seed.gender,
                birthday=date.fromisoformat(user_seed.birthday),
                bio=user_seed.bio,
                show_full_name=user_seed.show_full_name,
                show_gender=user_seed.show_gender,
                show_birthday=user_seed.show_birthday,
                show_email=user_seed.show_email,
                show_bio=user_seed.show_bio,
            )
        )
        session.commit()
        usernames[slug] = username
        summary.users += 1

    circle_ids: Dict[str, int] = {}
    tag_ids: Dict[Tuple[str, str], int] = {}
    team_ids: Dict[str, int] = {}

    for circle_seed in blueprint.circles:
        freedom_source_tags = circle_seed.freedom_source_tags or circle_seed.user_tags
        creator_id = _get_user_id(session, usernames[circle_seed.creator])
        circle = Circle(
            name=seed_circle_name(dataset, circle_seed.name),
            description=circle_seed.description,
            category=circle_seed.category,
            creator_id=creator_id,
        )
        session.add(circle)
        session.commit()
        session.refresh(circle)
        if circle.id is None:
            raise ValueError(f"Circle ID missing for {circle_seed.slug}")
        circle_ids[circle_seed.slug] = circle.id
        summary.circles += 1

        for member_slug in circle_seed.members:
            freedom_override = (circle_seed.member_freedom_profiles or {}).get(member_slug)
            if freedom_override is not None:
                freedom_text, freedom_profile = freedom_override
            else:
                freedom_text, freedom_profile = build_member_freedom_profile(
                    freedom_source_tags.get(member_slug, {}),
                    blueprint.users[member_slug].bio,
                )
            session.add(
                CircleMember(
                    user_id=_get_user_id(session, usernames[member_slug]),
                    circle_id=circle.id,
                    role=CircleRole.ADMIN if member_slug == circle_seed.creator else CircleRole.MEMBER,
                    freedom_tag_text=freedom_text,
                    freedom_tag_profile_json=encode_freedom_profile(freedom_profile),
                )
            )
        session.commit()

        for tag_seed in circle_seed.tags:
            tag = TagDefinition(
                circle_id=circle.id,
                name=tag_seed.name,
                data_type=tag_seed.data_type,
                required=tag_seed.required,
                options=_options(tag_seed.options),
                max_selections=tag_seed.max_selections,
                description=tag_seed.description,
            )
            session.add(tag)
            session.commit()
            session.refresh(tag)
            if tag.id is None:
                raise ValueError(f"Tag ID missing for {circle_seed.slug}:{tag_seed.name}")
            tag_ids[(circle_seed.slug, tag_seed.name)] = tag.id
            summary.tags += 1

        for member_slug, values in circle_seed.user_tags.items():
            for tag_name, value in values.items():
                session.add(
                    UserTag(
                        user_id=_get_user_id(session, usernames[member_slug]),
                        circle_id=circle.id,
                        tag_definition_id=tag_ids[(circle_seed.slug, tag_name)],
                        value=_normalize_tag_value(value),
                    )
                )
                summary.user_tags += 1
        session.commit()

        for team_seed in circle_seed.teams:
            creator_user_id = _get_user_id(session, usernames[team_seed.creator])
            if team_seed.freedom_text is not None and team_seed.freedom_keywords is not None:
                freedom_text = team_seed.freedom_text
                freedom_profile = {"keywords": team_seed.freedom_keywords[:5]}
            else:
                freedom_text, freedom_profile = build_team_freedom_profile(
                    team_seed,
                    freedom_source_tags.get(team_seed.creator, {}),
                )
            team = Team(
                name=seed_team_name(dataset, team_seed.name),
                description=team_seed.description,
                circle_id=circle.id,
                creator_id=creator_user_id,
                max_members=team_seed.max_members,
                required_tags_json=encode_required_tags(team_seed.required_tags),
                required_tag_rules_json=encode_required_tag_rules(team_seed.required_tag_rules),
                freedom_requirement_text=freedom_text,
                freedom_requirement_profile_json=encode_freedom_profile(freedom_profile),
            )
            session.add(team)
            session.commit()
            session.refresh(team)
            if team.id is None:
                raise ValueError(f"Team ID missing for {team_seed.slug}")
            team_ids[team_seed.slug] = team.id
            summary.teams += 1

            for member_slug in team_seed.members:
                session.add(
                    TeamMember(
                        team_id=team.id,
                        user_id=_get_user_id(session, usernames[member_slug]),
                    )
                )
                summary.team_members += 1
            if len(team_seed.members) >= team_seed.max_members:
                team.status = TeamStatus.LOCKED
                session.add(team)
            session.commit()

        for invitation_seed in circle_seed.invitations:
            invitation = Invitation(
                team_id=team_ids[invitation_seed.team_slug],
                inviter_id=_get_user_id(session, usernames[invitation_seed.inviter]),
                invitee_id=_get_user_id(session, usernames[invitation_seed.invitee]),
                kind=invitation_seed.kind,
                status=invitation_seed.status,
            )
            session.add(invitation)
            summary.invitations += 1
            if invitation_seed.status == InvitationStatus.ACCEPTED:
                joined_user_id = (
                    _get_user_id(session, usernames[invitation_seed.invitee])
                    if invitation_seed.kind == InvitationKind.INVITE
                    else _get_user_id(session, usernames[invitation_seed.inviter])
                )
                existing = session.exec(
                    select(TeamMember).where(
                        TeamMember.team_id == team_ids[invitation_seed.team_slug],
                        TeamMember.user_id == joined_user_id,
                    )
                ).first()
                if existing is None:
                    session.add(
                        TeamMember(
                            team_id=team_ids[invitation_seed.team_slug],
                            user_id=joined_user_id,
                        )
                    )
                    summary.team_members += 1
            session.commit()

    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed demo or stress data into the Boundary Circle database.")
    parser.add_argument("dataset", choices=["demo", "stress", "stress2"], help="Seed dataset to manage.")
    parser.add_argument("--reset", action="store_true", help="Delete the selected dataset without recreating it.")
    return parser.parse_args()


def format_summary(action: str, dataset: str, summary: SeedSummary) -> str:
    return (
        f"{action} {dataset}: "
        f"users={summary.users}, circles={summary.circles}, tags={summary.tags}, "
        f"user_tags={summary.user_tags}, teams={summary.teams}, "
        f"team_members={summary.team_members}, invitations={summary.invitations}"
    )


def main() -> int:
    args = parse_args()
    create_db_and_tables()
    with Session(engine) as session:
        if args.reset:
            summary = reset_dataset(session, args.dataset)
            print(format_summary("reset", args.dataset, summary))
            return 0

        summary = seed_dataset(session, args.dataset)
        print(format_summary("seeded", args.dataset, summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
