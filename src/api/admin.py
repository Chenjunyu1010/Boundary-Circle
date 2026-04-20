from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from scripts.seed_data import SeedSummary, reset_dataset, seed_dataset
from src.core.settings import Settings, get_settings
from src.db.database import get_session


router = APIRouter(prefix="/admin", tags=["Admin"])

DatasetName = Literal["demo", "stress", "stress2"]


class SeedSummaryResponse(BaseModel):
    users: int
    circles: int
    tags: int
    user_tags: int
    teams: int
    team_members: int
    invitations: int


class AdminSeedResponse(BaseModel):
    action: Literal["seed", "reset"]
    dataset: DatasetName
    summary: SeedSummaryResponse


def _require_admin_seed_key(
    x_admin_key: Optional[str] = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.admin_seed_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin seed API is not configured",
        )
    if x_admin_key != settings.admin_seed_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin key",
        )


def _build_seed_response(action: Literal["seed", "reset"], dataset: DatasetName, summary: SeedSummary) -> AdminSeedResponse:
    return AdminSeedResponse(
        action=action,
        dataset=dataset,
        summary=SeedSummaryResponse(
            users=summary.users,
            circles=summary.circles,
            tags=summary.tags,
            user_tags=summary.user_tags,
            teams=summary.teams,
            team_members=summary.team_members,
            invitations=summary.invitations,
        ),
    )


@router.post("/seed", response_model=AdminSeedResponse)
def admin_seed_dataset(
    dataset: DatasetName,
    _: None = Depends(_require_admin_seed_key),
    session: Session = Depends(get_session),
) -> AdminSeedResponse:
    summary = seed_dataset(session, dataset)
    return _build_seed_response("seed", dataset, summary)


@router.post("/seed/reset", response_model=AdminSeedResponse)
def admin_reset_seed_dataset(
    dataset: DatasetName,
    _: None = Depends(_require_admin_seed_key),
    session: Session = Depends(get_session),
) -> AdminSeedResponse:
    summary = reset_dataset(session, dataset)
    return _build_seed_response("reset", dataset, summary)
