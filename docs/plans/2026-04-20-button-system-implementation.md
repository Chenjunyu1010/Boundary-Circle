# Button System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Unify all Streamlit button styles into a clean product-style system that stays legible in both light and dark modes.

**Architecture:** Centralize button styling in `frontend/utils/ui.py` with explicit shared design tokens and variant rules for primary, secondary, page-link, and danger actions. Keep page-level changes limited to semantic button-type normalization plus danger markers for destructive actions.

**Tech Stack:** Streamlit, shared CSS injected through `st.markdown`, pytest frontend module tests.

---

### Task 1: Lock the new button contract with tests

**Files:**
- Modify: `tests/test_frontend_auth.py`

**Step 1: Write the failing test**

- Assert that shared button CSS defines `--bc-button-*` design tokens.
- Assert that default buttons use explicit background and border tokens rather than `currentColor` border mixing.
- Assert that danger-button marker CSS exists for destructive actions.

**Step 2: Run test to verify it fails**

Run: `pytest -v tests/test_frontend_auth.py::test_ui_button_css_defines_stable_product_button_tokens tests/test_frontend_auth.py::test_ui_button_variant_marker_renders_danger_hook`

Expected: FAIL because the current CSS still uses the old token mix and no danger marker helper exists.

**Step 3: Write minimal implementation**

- Add the new shared CSS tokens and variant selectors in `frontend/utils/ui.py`.
- Add a helper to emit a marker before destructive buttons.

**Step 4: Run test to verify it passes**

Run: `pytest -v tests/test_frontend_auth.py::test_ui_button_css_defines_stable_product_button_tokens tests/test_frontend_auth.py::test_ui_button_variant_marker_renders_danger_hook`

Expected: PASS

### Task 2: Normalize shared button hierarchy

**Files:**
- Modify: `frontend/utils/ui.py`

**Step 1: Update the shared button CSS**

- Define stable neutral, primary, focus, and danger tokens.
- Keep `page_link` visually aligned with neutral buttons.
- Use the danger marker selector to style destructive buttons without depending on theme-primary colors.

**Step 2: Re-run targeted tests**

Run: `pytest -v tests/test_frontend_auth.py::test_ui_button_css_defines_stable_product_button_tokens tests/test_frontend_auth.py::test_ui_button_variant_marker_renders_danger_hook`

Expected: PASS

### Task 3: Apply semantic button variants across pages

**Files:**
- Modify: `frontend/pages/profile.py`
- Modify: `frontend/views/circle_detail.py`
- Modify: `frontend/pages/team_management.py`

**Step 1: Normalize button intent**

- Use `primary` for create, save, submit, join, invite, approve, and recommendation actions.
- Keep view, back, cancel, and navigation actions neutral.
- Mark delete, reject, and leave actions as danger actions with the shared helper.

**Step 2: Verify no page logic changes**

- Confirm only button styling intent changed.
- Preserve keys and existing callbacks.

### Task 4: Verify the regression surface

**Files:**
- Test: `tests/test_frontend_auth.py`

**Step 1: Run focused frontend tests**

Run: `pytest -v tests/test_frontend_auth.py`

**Step 2: Review output**

- Confirm the CSS tests pass.
- Confirm the existing auth/profile frontend tests still pass.
