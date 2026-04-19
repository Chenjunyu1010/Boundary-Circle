from src.models.teams import (
    decode_freedom_profile,
    encode_freedom_profile,
    normalize_freedom_profile,
    empty_freedom_profile,
)


def test_empty_freedom_profile_returns_keywords_only():
    result = empty_freedom_profile()
    assert result == {"keywords": []}


def test_normalize_freedom_profile_handles_empty_input():
    result = normalize_freedom_profile(None)
    assert result == {"keywords": []}


def test_normalize_freedom_profile_handles_invalid_json():
    result = normalize_freedom_profile("not json")
    assert result == {"keywords": []}


def test_normalize_freedom_profile_dedupes_and_caps_keywords():
    raw = {"keywords": ["a", "b", "a", "c", "d", "e", "f", "g"]}
    result = normalize_freedom_profile(raw)
    # Only 5 allowed, dups removed
    assert len(result["keywords"]) == 5
    assert "a" in result["keywords"]
    assert set(result["keywords"]) <= {"a", "b", "c", "d", "e"}


def test_normalize_freedom_profile_ignores_unknown_keys():
    raw = {"keywords": ["a"], "traits": ["b"], "domains": ["c"], "unknown": ["x"]}
    result = normalize_freedom_profile(raw)
    # Only keywords supported in v1
    assert result == {"keywords": ["a"]}


def test_decode_freedom_profile_falls_back_to_empty_for_invalid():
    result = decode_freedom_profile('{"keywords": "not a list"}')
    assert result == {"keywords": []}


def test_encode_and_decode_roundtrip():
    profile = {"keywords": ["a", "b", "c"]}
    encoded = encode_freedom_profile(profile)
    decoded = decode_freedom_profile(encoded)
    assert decoded == profile
