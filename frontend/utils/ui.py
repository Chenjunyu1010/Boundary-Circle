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
            border: 1px solid #374151;
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
            border-color: #111827;
            box-shadow: 0 0 0 1px #111827 inset;
        }

        .stButton > button:focus,
        .stFormSubmitButton > button:focus {
            outline: 3px solid #93c5fd !important;
            outline-offset: 1px;
        }

        .stButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"] {
            background: #0b67c2;
            color: #ffffff;
            border-color: #0b67c2;
        }

        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button[kind="primary"]:hover {
            background: #08529a;
            border-color: #08529a;
            box-shadow: none;
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
            border: 1px solid #94a3b8;
            background: #f8fafc;
            font-weight: 620;
            text-decoration: none;
        }

        [data-testid="stPageLink"] a:hover {
            background: #eef2ff;
            border-color: #64748b;
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
