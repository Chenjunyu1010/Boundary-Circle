from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.settings import get_settings
from src.services.extraction import build_freedom_profile_extractor

CORPUS_PATH = ROOT / "docs" / "LLM-test" / "corpus.json"
RESULTS_DIR = ROOT / "docs" / "LLM-test" / "results"


def load_corpus(corpus_path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    samples = payload.get("samples", [])
    corpus: dict[str, dict[str, Any]] = {}
    for sample in samples:
        sample_id = str(sample["id"])
        corpus[sample_id] = {
            "id": sample_id,
            "name": str(sample["name"]),
            "input": str(sample["input"]),
            "expected": [str(item) for item in sample.get("expected", [])],
            "notes": str(sample.get("notes", "")),
            "language": str(sample.get("language", "")),
        }
    return corpus


def next_result_path(results_dir: Path) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    max_id = 0
    for path in results_dir.glob("R*.json"):
        suffix = path.stem[1:]
        if suffix.isdigit():
            max_id = max(max_id, int(suffix))
    next_id = max_id + 1
    return results_dir / f"R{next_id:03d}.json"


def classify_status(precision: float, recall: float) -> str:
    if precision == 1.0 and recall == 1.0:
        return "PASS"
    if precision == 0.0 and recall == 0.0:
        return "FAIL"
    return "PARTIAL"


def run_sample(sample_id: str, corpus_path: Path = CORPUS_PATH, results_dir: Path = RESULTS_DIR) -> Path:
    corpus = load_corpus(corpus_path)
    if sample_id not in corpus:
        raise KeyError(f"Unknown sample id: {sample_id}")

    sample = corpus[sample_id]
    extractor = build_freedom_profile_extractor()
    if extractor is None:
        raise RuntimeError("Extractor is not configured")

    settings = get_settings()
    result = extractor.extract_keywords(sample["input"])
    expected = [str(item) for item in sample["expected"]]
    actual = [str(item) for item in result.get("keywords", [])]

    expected_set = {item.strip().lower() for item in expected if item.strip()}
    actual_set = {item.strip().lower() for item in actual if item.strip()}
    overlap = sorted(expected_set & actual_set)
    precision = round(len(overlap) / len(actual_set), 2) if actual_set else 0.0
    recall = round(len(overlap) / len(expected_set), 2) if expected_set else 0.0
    status = classify_status(precision, recall)

    output_path = next_result_path(results_dir)
    payload = {
        "run_id": output_path.stem,
        "sample_id": sample["id"],
        "sample_name": sample["name"],
        "language": sample["language"],
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "base_url": settings.llm_base_url,
        "status": status,
        "input": sample["input"],
        "expected": expected,
        "actual": actual,
        "matched_expected": overlap,
        "metrics": {
            "precision": precision,
            "recall": recall,
        },
        "notes": sample["notes"],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one LLM extraction sample from docs/LLM-test/corpus.json")
    parser.add_argument("sample_id", help="Sample id, for example S001")
    args = parser.parse_args()

    output_path = run_sample(sample_id=args.sample_id)
    print(output_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
