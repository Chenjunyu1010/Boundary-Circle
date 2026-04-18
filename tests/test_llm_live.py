from __future__ import annotations

import os

import pytest


pytestmark = [
    pytest.mark.llm_live,
    pytest.mark.skipif(
        os.getenv("RUN_LLM_LIVE_TESTS") != "1",
        reason="live LLM tests are disabled by default",
    ),
]


def test_llm_live_placeholder() -> None:
    """Placeholder for future real-provider tests.

    Real LLM validation should stay opt-in because it depends on:
    - network access
    - valid API credentials
    - provider stability
    - model/version drift
    """

    assert True
