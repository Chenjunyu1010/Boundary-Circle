"""Shared Streamlit navigation registry and helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import streamlit as st


HOME_PAGE_FALLBACK = Path(__file__).with_name("Home.py").name
_registered_pages: dict[str, object] | None = None


def register_navigation(home_page_callable: Callable[[], None]) -> list[object]:
    """Register the app navigation pages once and return them in display order."""
    global _registered_pages

    if _registered_pages is None:
        _registered_pages = {
            "home": st.Page(home_page_callable, title="Home", icon="🏠", default=True),
            "circles": st.Page("pages/circles.py", title="Circle Hall", icon="🌐"),
            "profile": st.Page("pages/profile.py", title="My Profile", icon="👤"),
            "auth": st.Page(
                "pages/auth.py",
                title="Login / Register",
                icon="🔐",
                visibility="hidden",
            ),
            "public_profile": st.Page(
                "pages/public_profile.py",
                title="Public Profile",
                icon="🪪",
                visibility="hidden",
            ),
            "team_management": st.Page(
                "pages/team_management.py",
                title="Team Management",
                icon="👥",
                visibility="hidden",
            ),
        }

    return list(_registered_pages.values())


def get_navigation_page(key: str) -> object:
    """Return a previously registered page, or a safe fallback when unavailable."""
    if _registered_pages and key in _registered_pages:
        return _registered_pages[key]

    if key == "home":
        return HOME_PAGE_FALLBACK

    raise KeyError(f"Unknown navigation page: {key}")
