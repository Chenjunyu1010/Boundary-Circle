# LLM Testing Summary

## Model History

- Initial real-provider validation used `qwen3.5-plus`.
- Early testing showed that `qwen3.5-plus` could return very good exact keywords on some clear English samples, but it was often unstable in practice.
- The main operational problem was repeated timeout or connection interruption during live calls, especially when testing short Chinese samples.
- To improve turnaround speed and reduce interruption risk during manual sample-by-sample validation, the active test model was switched to `qwen3-coder-next`.
- After the switch, response stability improved enough to continue iterative testing and prompt tuning.

## Fixes Made During Testing

- Added structured timeout configuration and one retry for transient `ReadTimeout`, `ConnectTimeout`, and `ConnectError`.
- Tightened the base prompt to prefer exact wording from the input text.
- Added prompt constraints to avoid broader paraphrases and inferred categories.
- Added prompt constraints to exclude explicitly disliked or rejected items.
- Added prompt constraints to exclude generic action or filler words such as `help`, `stable`, `work`, and `learn`.
- Rebuilt the LLM corpus as `docs/LLM-test/corpus.json` and fixed Chinese text corruption by treating the corpus as the single source of truth.
- Switched to `docs/LLM-test/results/Rxxx.json` so every live run is preserved as its own artifact.
- Removed redundant retry-only historical files that did not add new coverage.

## Scenarios Considered

- Clear positive English technical sentence
- Clear positive Chinese technical sentence
- English negation sentence
- Chinese negation sentence
- Weak-signal English sentence
- Chinese skill sentence with Chinese expected keywords
- Ambiguous Chinese interest sentence
- Ambiguous Chinese systems/performance sentence
- Long Chinese sentence containing more than 5 valid keywords

## Current Scenario Results

- `S001` clear English technical sentence: stable `PASS`
- `S002` English negation:
  - old prompt result `R016`: `PARTIAL`, wrongly included `frontend`
  - tightened prompt result `R019`: `PASS`
- `S003` clear Chinese technical sentence: `PASS` in `R018`
- `S004` Chinese negation:
  - before cleanup/prompt stabilization there were corrupted or partial references
  - tightened prompt result `R020`: `PASS`
- `S005` weak-signal English sentence: `PARTIAL` in `R015`
  - core concepts were captured
  - generic extras such as `stable` and `help` were also returned before prompt tightening was fully evaluated on this sample
- `S006` Chinese skill sentence with Chinese keywords: `PASS` in `R021`
- `S007` ambiguous Chinese interest sentence: `PARTIAL` in `R022`
  - model returned `偏底层` instead of strict expected `底层`
  - semantically close, but not exact-match identical
- `S008` ambiguous Chinese systems/performance sentence: `PARTIAL` in `R023`
  - model returned `系统开发` instead of strict expected `系统`
  - again close in meaning, but more specific than expected
- `S009` long Chinese sentence with 10 valid concepts: `PARTIAL` in `R024`
  - actual result kept only 5 items
  - this is consistent with current product logic, which caps keywords at 5

## Main Conclusions

- For clear positive statements, the current setup is strong in both English and Chinese.
- The largest early operational issue was not raw extraction quality but instability and interruption when using the heavier model.
- Switching to `qwen3-coder-next` materially improved practical testing flow.
- Prompt tightening successfully fixed the main negation failure mode in both English and Chinese.
- Ambiguous sentences remain harder to score with exact-match metrics because the model tends to make small semantic refinements such as:
  - `底层` -> `偏底层`
  - `系统` -> `系统开发`
- Long sentences are currently limited more by product design than by model understanding, because output is capped at 5 keywords.

## Evaluation Notes

- Exact-match precision/recall is useful for clear samples.
- For ambiguous samples, exact-match metrics should be read together with manual semantic judgment.
- For long samples, low recall may simply reflect the hard 5-keyword cap rather than model failure.

## Recommended Next Steps

- Re-test `S005` after the latest prompt tightening to see whether weak-signal over-extraction has improved.
- If ambiguous-sample evaluation becomes important, introduce a separate semantic-match review field instead of relying only on exact-match metrics.
- If long-profile coverage matters in the product, consider raising the keyword cap from 5 to 8 or 10 and then re-running `S009`.
