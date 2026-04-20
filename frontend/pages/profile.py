"""
Dedicated profile page for viewing and editing the current user's profile.
"""

from __future__ import annotations

import calendar
import sys
from pathlib import Path
from typing import Optional

import streamlit as st

parent_dir = str(Path(__file__).resolve().parents[1])
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.api import api_client, response_json_object
from utils.auth import require_auth
from utils.ui import apply_button_usability_style
from navigation import get_navigation_page


GENDER_OPTIONS = ["Male", "Female", "Other", "Prefer not to say"]


def normalize_gender_value(value: Optional[str]) -> str:
    if not value:
        return "Prefer not to say"
    if value not in GENDER_OPTIONS:
        return "Prefer not to say"
    return value


def split_birthday_parts(value: Optional[str]) -> tuple[Optional[int], Optional[int], Optional[int]]:
    if not value:
        return None, None, None
    try:
        year_text, month_text, day_text = value.split("-")
        return int(year_text), int(month_text), int(day_text)
    except (TypeError, ValueError):
        return None, None, None


def compose_birthday(
    year: Optional[int], month: Optional[int], day: Optional[int]
) -> Optional[str]:
    if year is None or month is None or day is None:
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def get_birthday_day_options(
    year: Optional[int], month: Optional[int]
) -> list[Optional[int]]:
    """Return valid day choices for the selected month and year."""
    if year is None or month is None:
        return [None] + list(range(1, 32))
    _, max_day = calendar.monthrange(year, month)
    return [None] + list(range(1, max_day + 1))


def load_profile() -> Optional[dict]:
    response = api_client.get("/profile/me")
    if not response.ok:
        st.error(f"Failed to load profile: {getattr(response, 'reason', 'Unknown error')}")
        return None
    return response_json_object(response)


def main():
    apply_button_usability_style()
    require_auth()
    st.title("My Profile")
    st.caption("Manage your personal details and choose what other users can see.")

    profile = load_profile()
    if profile is None:
        return

    gender_value = normalize_gender_value(profile.get("gender"))
    selected_year, selected_month, selected_day = split_birthday_parts(profile.get("birthday"))
    year_options = [None] + list(range(1980, 2011))
    month_options = [None] + list(range(1, 13))

    with st.form("profile_form"):
        full_name = st.text_input("Full name", value=profile.get("full_name") or "")
        gender = st.selectbox(
            "Gender",
            options=GENDER_OPTIONS,
            index=GENDER_OPTIONS.index(gender_value),
        )
        st.caption("Birthday")
        year_col, month_col, day_col = st.columns(3)
        with year_col:
            birthday_year = st.selectbox(
                "Year",
                options=year_options,
                index=year_options.index(selected_year) if selected_year in year_options else 0,
                format_func=lambda value: "Year" if value is None else str(value),
            )
        with month_col:
            birthday_month = st.selectbox(
                "Month",
                options=month_options,
                index=month_options.index(selected_month) if selected_month in month_options else 0,
                format_func=lambda value: "Month" if value is None else str(value),
            )
        day_options = get_birthday_day_options(birthday_year, birthday_month)
        with day_col:
            birthday_day = st.selectbox(
                "Day",
                options=day_options,
                index=day_options.index(selected_day) if selected_day in day_options else 0,
                format_func=lambda value: "Day" if value is None else str(value),
            )
        bio = st.text_area("Bio", value=profile.get("bio") or "", max_chars=300)

        st.markdown("### Visibility")
        show_full_name = st.checkbox("Show full name", value=profile.get("show_full_name", True))
        show_gender = st.checkbox("Show gender", value=profile.get("show_gender", True))
        show_birthday = st.checkbox("Show birthday", value=profile.get("show_birthday", True))
        show_email = st.checkbox("Show email", value=profile.get("show_email", True))
        show_bio = st.checkbox("Show bio", value=profile.get("show_bio", True))

        submitted = st.form_submit_button("💾 Save profile")

    if not submitted:
        return

    payload = {
        "full_name": full_name or None,
        "gender": gender or None,
        "birthday": compose_birthday(birthday_year, birthday_month, birthday_day),
        "bio": bio or None,
        "show_full_name": show_full_name,
        "show_gender": show_gender,
        "show_birthday": show_birthday,
        "show_email": show_email,
        "show_bio": show_bio,
    }

    response = api_client.put("/profile/me", data=payload)
    if response.ok:
        updated_profile = response_json_object(response)
        st.session_state.full_name = updated_profile.get("full_name")
        st.session_state.show_profile_completion_prompt = False
        st.success("Profile updated.")
        st.switch_page(get_navigation_page("home"))
        return

    detail = getattr(response, "reason", "Unknown error")
    try:
        detail = response_json_object(response).get("detail", detail)
    except Exception:
        pass
    st.error(f"Failed to update profile: {detail}")


if __name__ == "__main__":
    main()
