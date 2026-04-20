"""Shared UI helpers for Streamlit page readability."""

from __future__ import annotations

import streamlit as st


def build_button_usability_css() -> str:
    """Return shared button CSS used across Streamlit pages."""
    return """
        <style>
        :root {
            --bc-button-bg: var(--st-secondary-background-color);
            --bc-button-text: var(--st-text-color);
            --bc-button-border: var(--st-border-color);
            --bc-button-hover-border: color-mix(in srgb, var(--st-text-color) 40%, var(--st-border-color));
            --bc-button-hover-bg: color-mix(
                in srgb,
                var(--st-secondary-background-color) 78%,
                var(--st-text-color) 22%
            );
            --bc-button-focus: color-mix(in srgb, var(--st-primary-color) 45%, white);
            --bc-primary-button-bg: var(--st-primary-color);
            --bc-primary-button-text: var(--st-background-color);
            --bc-primary-button-hover-bg: color-mix(in srgb, var(--st-primary-color) 84%, black);
            --bc-page-link-bg: var(--st-secondary-background-color);
            --bc-page-link-text: var(--st-text-color);
            --bc-page-link-border: var(--st-border-color);
            --bc-page-link-hover-bg: color-mix(
                in srgb,
                var(--st-secondary-background-color) 72%,
                var(--st-primary-color) 28%
            );
            --bc-page-link-hover-border: color-mix(in srgb, var(--st-primary-color) 50%, var(--st-border-color));
        }

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
            border: 1px solid var(--bc-button-border);
            background: var(--bc-button-bg);
            color: var(--bc-button-text);
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
            border-color: var(--bc-button-hover-border);
            background: var(--bc-button-hover-bg);
            color: var(--bc-button-text);
            box-shadow: 0 0 0 1px var(--bc-button-hover-border) inset;
        }

        .stButton > button:focus,
        .stFormSubmitButton > button:focus {
            outline: 3px solid var(--bc-button-focus) !important;
            outline-offset: 1px;
        }

        .stButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"] {
            background: var(--bc-primary-button-bg);
            color: var(--bc-primary-button-text);
            border-color: var(--bc-primary-button-bg);
        }

        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button[kind="primary"]:hover {
            background: var(--bc-primary-button-hover-bg);
            color: var(--bc-primary-button-text);
            border-color: var(--bc-primary-button-hover-bg);
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
            border: 1px solid var(--bc-page-link-border);
            background: var(--bc-page-link-bg);
            color: var(--bc-page-link-text);
            font-weight: 620;
            text-decoration: none;
        }

        [data-testid="stPageLink"] a:hover {
            background: var(--bc-page-link-hover-bg);
            color: var(--bc-page-link-text);
            border-color: var(--bc-page-link-hover-border);
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
