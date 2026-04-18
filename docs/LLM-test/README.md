# LLM Test Assets

This directory stores small-sample validation assets for freedom keyword extraction.

## Files

- `corpus.json`: source-of-truth sample library
- `results/Rxxx.json`: one real test result per run
- `SUMMARY.md`: consolidated testing summary, covered scenarios, and change history

## Rules

- Keep corpus text in UTF-8.
- Each run should execute only one sample.
- Do not overwrite old result files.
- Result files should stay brief and map back to `sample_id`.

## Run

```bash
python scripts/run_llm_sample.py S001
```

The script reads `docs/LLM-test/corpus.json` and writes the next result file under `docs/LLM-test/results/`.

## CI Policy

- Default CI must not depend on a real LLM provider.
- Real LLM tests should use the `llm_live` pytest marker.
- GitHub Actions excludes `llm_live` tests by default.
- If maintainers want to run real-provider tests manually, set `RUN_LLM_LIVE_TESTS=1` and invoke pytest explicitly for those tests.

## Problem Fix Log

- `2026-04-19`: Added timeout and retry handling in the OpenAI-compatible extractor to reduce transient request failures.
- `2026-04-19`: Tightened the extraction prompt to prefer exact wording, avoid broader paraphrases, and keep output language aligned with input.
- `2026-04-19`: Added explicit prompt rules to exclude negative preferences such as disliked or rejected items.
- `2026-04-19`: Added explicit prompt rules to exclude generic action words or filler terms such as `help`, `stable`, `work`, and `learn`.
- `2026-04-19`: Rebuilt `docs/LLM-test/corpus.json` as the single source of truth for sample texts and fixed Chinese sample encoding corruption.
- `2026-04-19`: Switched to one-result-per-run logging under `docs/LLM-test/results/Rxxx.json`.
- `2026-04-19`: Removed redundant historical retry-only result files that did not add new sample coverage.

## Example Impact

- `R016` showed the old prompt still extracted `frontend` from the negative sentence in sample `S002`.
- `R019` showed the tightened prompt fixed that case and returned only `Python` and `SQL`.
