"""Shared UI helpers for Streamlit page readability."""

from __future__ import annotations

import streamlit as st


def build_button_usability_css() -> str:
    """Return shared button CSS used across Streamlit pages."""
    return """
        <style>
        /* Hide browser-native password reveal controls so Streamlit shows only one toggle. */
        input[type="password"]::-ms-reveal,
        input[type="password"]::-ms-clear {
            display: none;
        }

        .stButton > button,
        .stFormSubmitButton > button {
            min-height: 2.75rem;
            width: 100%;
            padding: 0.45rem 1rem;
            border-radius: 10px;
            font-weight: 650;
            letter-spacing: 0.01em;
            transition: all 0.15s ease;
            white-space: normal;
            overflow-wrap: anywhere;
            line-height: 1.25;
            justify-content: center;
            text-align: center;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            box-shadow: 0 0 0 1px currentColor inset;
        }

        .stButton > button:focus,
        .stFormSubmitButton > button:focus {
            outline: 3px solid color-mix(in srgb, var(--st-primary-color) 45%, white) !important;
            outline-offset: 1px;
        }

        .bc-compact-action button {
            min-height: 2.5rem;
            padding: 0.35rem 0.65rem;
            font-size: 0.92rem;
        }

        .bc-nowrap-action button {
            white-space: nowrap;
            overflow-wrap: normal;
        }

        [data-testid="stPageLink"] a {
            display: inline-flex;
            align-items: center;
            min-height: 2.5rem;
            padding: 0.45rem 0.8rem;
            border-radius: 10px;
            font-weight: 620;
            text-decoration: none;
        }

        [data-testid="stPageLink"] a:hover {
            box-shadow: 0 0 0 1px currentColor inset;
        }
        </style>
        """


def apply_button_usability_style() -> None:
    """Apply a consistent high-contrast style for actions and navigation links.

    This style improves quick visual recognition of clickable controls while
    keeping the existing page logic unchanged.
    """
    st.markdown(
        build_button_usability_css(),
        unsafe_allow_html=True,
    )
