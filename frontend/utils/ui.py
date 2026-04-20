"""Shared UI helpers for Streamlit page readability."""

from __future__ import annotations

import streamlit as st


def build_button_usability_css() -> str:
    """Return shared button CSS used across Streamlit pages."""
    return """
        <style>
        :root {
            --bc-button-primary-bg: color-mix(
                in srgb,
                var(--st-background-color, #ffffff) 78%,
                var(--st-text-color, #111827) 22%
            );
            --bc-button-primary-bg-hover: color-mix(
                in srgb,
                var(--st-background-color, #ffffff) 68%,
                var(--st-text-color, #111827) 32%
            );
            --bc-button-primary-border: color-mix(
                in srgb,
                var(--st-background-color, #ffffff) 52%,
                var(--st-text-color, #111827) 48%
            );
            --bc-button-primary-text: #ffffff;
            --bc-button-neutral-bg: color-mix(
                in srgb,
                var(--st-background-color, #ffffff) 92%,
                #64748b 8%
            );
            --bc-button-neutral-bg-hover: color-mix(
                in srgb,
                var(--st-background-color, #ffffff) 86%,
                #64748b 14%
            );
            --bc-button-neutral-border: color-mix(
                in srgb,
                var(--st-border-color, #cbd5e1) 72%,
                #64748b 28%
            );
            --bc-button-danger-bg: color-mix(
                in srgb,
                var(--st-background-color, #ffffff) 72%,
                #3f0d12 28%
            );
            --bc-button-danger-bg-hover: color-mix(
                in srgb,
                var(--st-background-color, #ffffff) 62%,
                #3f0d12 38%
            );
            --bc-button-danger-border: color-mix(
                in srgb,
                var(--st-background-color, #ffffff) 48%,
                #3f0d12 52%
            );
            --bc-button-danger-text: #ffffff;
            --bc-button-focus-ring: color-mix(
                in srgb,
                var(--st-primary-color, #2563eb) 42%,
                white 58%
            );
            --bc-tab-accent: #dc2626;
            --bc-tab-active-bg: color-mix(
                in srgb,
                #dc2626 8%,
                var(--st-background-color, #ffffff) 86%
            );
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
            background: var(--bc-button-neutral-bg);
            color: inherit;
            border: 1px solid var(--bc-button-neutral-border) !important;
            border-radius: 10px;
            font-weight: 650;
            letter-spacing: 0.01em;
            box-shadow: 0 1px 0 rgba(15, 23, 42, 0.04);
            transition:
                background-color 0.15s ease,
                border-color 0.15s ease,
                box-shadow 0.15s ease,
                transform 0.15s ease;
            white-space: normal;
            overflow-wrap: anywhere;
            line-height: 1.25;
            justify-content: center;
            text-align: center;
        }

        .stButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"] {
            background: var(--bc-button-primary-bg) !important;
            color: var(--bc-button-primary-text) !important;
            border-color: var(--bc-button-primary-border) !important;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.22);
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            background: var(--bc-button-neutral-bg-hover);
            border-color: color-mix(in srgb, var(--bc-button-neutral-border) 82%, #475569 18%) !important;
            box-shadow: 0 0 0 1px rgba(100, 116, 139, 0.14) inset;
            transform: translateY(-1px);
        }

        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button[kind="primary"]:hover {
            background: var(--bc-button-primary-bg-hover) !important;
            border-color: var(--bc-button-primary-border) !important;
            box-shadow: 0 14px 28px rgba(15, 23, 42, 0.28);
        }

        button[role="tab"] {
            background: transparent !important;
            border: 1px solid transparent !important;
            border-bottom: 2px solid transparent !important;
            border-radius: 10px !important;
            box-shadow: none !important;
        }

        button[role="tab"]:hover {
            background: transparent !important;
            box-shadow: none !important;
        }

        button[role="tab"]:focus {
            outline: none !important;
            box-shadow: none !important;
        }

        button[role="tab"][aria-selected="true"] {
            background: transparent !important;
            color: var(--bc-tab-accent) !important;
            border-color: transparent !important;
            border-bottom-color: var(--bc-tab-accent) !important;
            box-shadow: none !important;
        }

        .stButton > button:focus,
        .stFormSubmitButton > button:focus,
        button[role="tab"]:focus {
            outline: 3px solid var(--bc-button-focus-ring) !important;
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

        .bc-button-marker {
            display: none;
        }

        div.element-container:has(.bc-button-marker[data-variant="danger"])
        + div.element-container .stButton > button,
        div.element-container:has(.bc-button-marker[data-variant="danger"])
        + div.element-container .stFormSubmitButton > button {
            background: var(--bc-button-danger-bg) !important;
            color: var(--bc-button-danger-text) !important;
            border-color: var(--bc-button-danger-border) !important;
            box-shadow: 0 10px 22px rgba(220, 38, 38, 0.22);
        }

        div.element-container:has(.bc-button-marker[data-variant="danger"])
        + div.element-container .stButton > button:hover,
        div.element-container:has(.bc-button-marker[data-variant="danger"])
        + div.element-container .stFormSubmitButton > button:hover {
            background: var(--bc-button-danger-bg-hover) !important;
            border-color: var(--bc-button-danger-border) !important;
            box-shadow: 0 14px 28px rgba(185, 28, 28, 0.28);
        }

        [data-testid="stPageLink"] a {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 2.5rem;
            padding: 0.45rem 0.8rem;
            background: var(--bc-button-neutral-bg);
            color: inherit;
            border: 1px solid var(--bc-button-neutral-border);
            border-radius: 10px;
            font-weight: 620;
            text-decoration: none;
            transition:
                background-color 0.15s ease,
                border-color 0.15s ease,
                box-shadow 0.15s ease,
                transform 0.15s ease;
        }

        [data-testid="stPageLink"] a:hover {
            background: var(--bc-button-neutral-bg-hover);
            border-color: color-mix(in srgb, var(--bc-button-neutral-border) 82%, #475569 18%);
            box-shadow: 0 0 0 1px rgba(100, 116, 139, 0.14) inset;
            transform: translateY(-1px);
        }
        </style>
        """


def apply_button_usability_style() -> None:
    """Apply a consistent high-contrast style for actions and navigation links."""
    st.markdown(
        build_button_usability_css(),
        unsafe_allow_html=True,
    )


def render_button_variant_marker(variant: str) -> None:
    """Render a hidden marker used to scope the next button variant style."""
    st.markdown(
        f'<div class="bc-button-marker" data-variant="{variant}"></div>',
        unsafe_allow_html=True,
    )
