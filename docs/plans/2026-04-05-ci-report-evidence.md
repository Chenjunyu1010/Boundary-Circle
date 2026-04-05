# CI and Report Evidence Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add report-friendly CI outputs and lightweight repository process improvements without changing product scope.

**Architecture:** Extend the existing single GitHub Actions workflow rather than redesigning it. Pair the workflow change with minimal documentation so generated evidence is easy to cite in the course report and in future pull requests.

**Tech Stack:** GitHub Actions, pytest, pytest-cov, Markdown docs

---

### Task 1: Upgrade CI Outputs

**Files:**
- Modify: `.github/workflows/ci.yml`

**Step 1: Keep the existing trigger model**

Preserve the current push and pull request triggers for `main`.

**Step 2: Add dependency caching**

Use `actions/setup-python` with `cache: pip` so repeat workflow runs are faster and easier to explain in the report.

**Step 3: Replace the test command**

Run:

```bash
pytest --junitxml=test-results/pytest.xml --cov=src --cov=frontend --cov-report=term-missing --cov-report=xml:coverage.xml
```

**Step 4: Upload artifacts**

Upload:

- `test-results/pytest.xml`
- `coverage.xml`

with `if: ${{ always() }}`.

### Task 2: Document Local and CI Evidence

**Files:**
- Modify: `README.md`
- Create: `docs/report-evidence.md`

**Step 1: Expand the testing section**

Add local commands for:

- quick test run
- focused test run
- coverage + JUnit generation

**Step 2: Add CI evidence guidance**

Document what the workflow now produces and how those outputs support the progress report.

**Step 3: Create a report evidence index**

Map report topics to concrete repository files such as:

- system summary and stack
- CI workflow
- test suite
- limitations and incomplete areas

### Task 3: Improve Pull Request Traceability

**Files:**
- Create: `.github/pull_request_template.md`

**Step 1: Add a minimal PR checklist**

Include fields for:

- change summary
- test evidence
- report impact
- screenshots or artifacts if relevant

This helps future PRs produce evidence that can be cited in report section 3 and section 5.

### Task 4: Verify

**Files:**
- No repository edits required

**Step 1: Run the baseline suite**

Run:

```bash
pytest -q
```

**Step 2: Run the CI-equivalent coverage command**

Run:

```bash
pytest --junitxml=test-results/pytest.xml --cov=src --cov=frontend --cov-report=term-missing --cov-report=xml:coverage.xml
```

**Step 3: Confirm outputs**

Check that:

- tests pass
- `test-results/pytest.xml` exists
- `coverage.xml` exists

### Task 5: Commit

**Files:**
- Stage the modified workflow, docs, and template

**Step 1: Commit**

```bash
git add .github/workflows/ci.yml .github/pull_request_template.md README.md docs/report-evidence.md docs/plans/2026-04-05-ci-report-evidence-design.md docs/plans/2026-04-05-ci-report-evidence.md
git commit -m "ci: add report-friendly test artifacts"
```
