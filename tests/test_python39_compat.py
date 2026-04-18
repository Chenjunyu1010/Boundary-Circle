from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_llm_related_files_parse_with_python39_grammar() -> None:
    target_files = [
        PROJECT_ROOT / "src" / "services" / "extraction.py",
        PROJECT_ROOT / "src" / "models" / "teams.py",
        PROJECT_ROOT / "src" / "api" / "teams.py",
        PROJECT_ROOT / "tests" / "test_extraction_service.py",
    ]

    for path in target_files:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path), feature_version=(3, 9))
