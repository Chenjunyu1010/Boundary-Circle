from __future__ import annotations

import json
from pathlib import Path

import httpx

import scripts.run_llm_sample as run_llm_sample


class _FakeExtractor:
    def extract_keywords(self, text: str) -> dict[str, list[str]]:
        return {"keywords": ["Python", "FastAPI"]}


def test_load_corpus_reads_utf8_chinese_text(monkeypatch) -> None:
    corpus_path = Path("virtual-corpus.json")
    payload = json.dumps(
        {
            "samples": [
                {
                    "id": "S003",
                    "name": "zh_short_tech",
                    "input": "我喜欢 Python、FastAPI 和数据库设计。",
                    "expected": ["Python", "FastAPI", "数据库设计"],
                }
            ]
        },
        ensure_ascii=False,
        indent=2,
    )

    monkeypatch.setattr(Path, "read_text", lambda self, encoding="utf-8": payload)

    corpus = run_llm_sample.load_corpus(corpus_path)

    assert corpus["S003"]["input"] == "我喜欢 Python、FastAPI 和数据库设计。"
    assert corpus["S003"]["expected"] == ["Python", "FastAPI", "数据库设计"]


def test_next_result_path_increments_numeric_suffix(monkeypatch) -> None:
    results_dir = Path("virtual-results")

    monkeypatch.setattr(Path, "mkdir", lambda self, parents=True, exist_ok=True: None)
    monkeypatch.setattr(
        Path,
        "glob",
        lambda self, pattern: [
            Path("R001.json"),
            Path("R012.json"),
        ],
    )

    next_path = run_llm_sample.next_result_path(results_dir)

    assert next_path.name == "R013.json"


def test_run_sample_writes_single_result_file(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        run_llm_sample,
        "load_corpus",
        lambda corpus_path: {
            "S001": {
                "id": "S001",
                "name": "en_backend",
                "language": "en",
                "input": "I enjoy Python, FastAPI, backend systems, distributed systems, and API design.",
                "expected": [
                    "Python",
                    "FastAPI",
                    "backend systems",
                    "distributed systems",
                    "API design",
                ],
                "notes": "",
            }
        },
    )
    monkeypatch.setattr(run_llm_sample, "build_freedom_profile_extractor", lambda: _FakeExtractor())
    monkeypatch.setattr(run_llm_sample, "next_result_path", lambda results_dir: Path("R001.json"))
    monkeypatch.setattr(
        run_llm_sample,
        "get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "llm_provider": "openai_compatible",
                "llm_model": "test-model",
                "llm_base_url": "https://example.test/v1",
            },
        )(),
    )

    def fake_write_text(self: Path, content: str, encoding: str = "utf-8") -> int:
        captured["path"] = str(self)
        captured["payload"] = json.loads(content)
        return len(content)

    monkeypatch.setattr(Path, "write_text", fake_write_text)

    output_path = run_llm_sample.run_sample(
        sample_id="S001",
        corpus_path=Path("virtual-corpus.json"),
        results_dir=Path("virtual-results"),
    )

    assert output_path.name == "R001.json"
    payload = captured["payload"]
    assert captured["path"] == "R001.json"
    assert payload["run_id"] == "R001"
    assert payload["sample_id"] == "S001"
    assert payload["sample_name"] == "en_backend"
    assert payload["status"] == "PARTIAL"
    assert payload["expected"] == [
        "Python",
        "FastAPI",
        "backend systems",
        "distributed systems",
        "API design",
    ]
    assert payload["actual"] == ["Python", "FastAPI"]
    assert payload["metrics"] == {"precision": 1.0, "recall": 0.4}


def test_run_sample_writes_timeout_result_file(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _TimeoutExtractor:
        def extract_keywords(self, text: str) -> dict[str, list[str]]:
            raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(
        run_llm_sample,
        "load_corpus",
        lambda corpus_path: {
            "S002": {
                "id": "S002",
                "name": "en_negation_short",
                "language": "en",
                "input": "I know Python and SQL, but I do not like frontend.",
                "expected": ["Python", "SQL"],
                "notes": "",
            }
        },
    )
    monkeypatch.setattr(run_llm_sample, "build_freedom_profile_extractor", lambda: _TimeoutExtractor())
    monkeypatch.setattr(run_llm_sample, "next_result_path", lambda results_dir: Path("R999.json"))
    monkeypatch.setattr(
        run_llm_sample,
        "get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "llm_provider": "openai_compatible",
                "llm_model": "test-model",
                "llm_base_url": "https://example.test/v1",
            },
        )(),
    )

    def fake_write_text(self: Path, content: str, encoding: str = "utf-8") -> int:
        captured["payload"] = json.loads(content)
        return len(content)

    monkeypatch.setattr(Path, "write_text", fake_write_text)

    output_path = run_llm_sample.run_sample(
        sample_id="S002",
        corpus_path=Path("virtual-corpus.json"),
        results_dir=Path("virtual-results"),
    )

    assert output_path.name == "R999.json"
    payload = captured["payload"]
    assert payload["status"] == "TIMEOUT"
    assert payload["actual"] == []
    assert payload["metrics"] == {"precision": 0.0, "recall": 0.0}
    assert payload["error_type"] == "ReadTimeout"
