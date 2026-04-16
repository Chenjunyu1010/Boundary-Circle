import importlib

import pytest


def _reload_settings_module():
    import src.core.settings as settings_module

    settings_module.get_settings.cache_clear()
    return importlib.reload(settings_module)


def _reload_security_module():
    import src.auth.security as security_module

    return importlib.reload(security_module)


def test_settings_use_ephemeral_secret_in_development(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("APP_ENV", "development")

    settings_module = _reload_settings_module()
    settings = settings_module.get_settings()

    assert settings.resolved_secret_key
    assert isinstance(settings.resolved_secret_key, str)


def test_settings_fail_fast_without_secret_in_production(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("APP_ENV", "production")

    settings_module = _reload_settings_module()
    settings = settings_module.get_settings()

    with pytest.raises(RuntimeError, match="SECRET_KEY must be configured"):
        _ = settings.resolved_secret_key


def test_security_module_respects_explicit_secret_key(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret-key")

    settings_module = _reload_settings_module()
    settings_module.get_settings.cache_clear()
    security_module = _reload_security_module()

    token = security_module.create_access_token("123")
    payload = security_module.decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "123"
