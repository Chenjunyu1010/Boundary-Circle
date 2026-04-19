# Stress Seed Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the `stress` dataset with 48 users, mixed circle types, float tags including GPA, and range-based numeric team rules.

**Architecture:** Replace the current narrow course/project-only stress blueprint with a multi-family dataset spanning study, sports, and entertainment circles. Use structured `TeamRequirementRule` payloads for numeric ranges so the seed matches current backend matching semantics.

**Tech Stack:** Python, SQLModel, pytest

---

### Task 1: Lock the new stress dataset contract with tests

**Files:**
- Modify: `tests/test_seed_data.py`

**Step 1: Write the failing test**

- Assert the new stress dataset creates 48 users and 8 circles.
- Assert `GPA` and at least one other float tag exist.
- Assert sports and entertainment categories exist.
- Assert at least one stress team stores numeric range rules.
- Assert at least one stress user joins multiple circles.

**Step 2: Run test to verify it fails**

Run: `pytest -v tests/test_seed_data.py::test_seed_stress_creates_varied_dataset`

**Step 3: Write minimal implementation**

- Rewrite `build_stress_dataset()`.

**Step 4: Run test to verify it passes**

Run: `pytest -v tests/test_seed_data.py::test_seed_stress_creates_varied_dataset`

**Step 5: Commit**

```bash
git add docs/plans/2026-04-20-stress-seed-redesign-design.md docs/plans/2026-04-20-stress-seed-redesign.md tests/test_seed_data.py scripts/seed_data.py
git commit -m "feat: redesign stress seed dataset"
```
