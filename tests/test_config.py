import os
import pytest
from pipeline.config import PipelineConfig, get_config


def test_pipeline_config_defaults(monkeypatch):
    """Verify that PipelineConfig provides sound defaults when env vars are unset."""
    monkeypatch.delenv("OUTREACH_EMAIL_USER", raising=False)
    monkeypatch.delenv("OUTREACH_EMAIL_PASSWORD", raising=False)
    monkeypatch.delenv("MIDTRANS_SERVER_KEY", raising=False)
    monkeypatch.delenv("VERCEL_TOKEN", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    cfg = PipelineConfig()
    assert cfg.email_host == "smtp.gmail.com"
    assert cfg.email_port == 587
    assert cfg.sender_name != ""
    assert cfg.has_gemini is False
    assert cfg.has_vercel is False
    assert cfg.has_midtrans is False
    assert cfg.has_email is False
    assert os.path.isabs(cfg.base_dir)
    assert os.path.isabs(cfg.clients_dir)
    assert os.path.isabs(cfg.db_path)


def test_pipeline_config_custom_env(monkeypatch):
    """Verify that PipelineConfig correctly reads custom environment variables."""
    monkeypatch.setenv("OUTREACH_EMAIL_USER", "test@domain.com")
    monkeypatch.setenv("OUTREACH_EMAIL_PASSWORD", "secret123")
    monkeypatch.setenv("MIDTRANS_SERVER_KEY", "SB-Mid-server-xxx")
    monkeypatch.setenv("VERCEL_TOKEN", "vcl_token_123")
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTest")
    monkeypatch.setenv("MIDTRANS_IS_PRODUCTION", "true")

    cfg = PipelineConfig()
    assert cfg.email_user == "test@domain.com"
    assert cfg.email_password == "secret123"
    assert cfg.midtrans_server_key == "SB-Mid-server-xxx"
    assert cfg.vercel_token == "vcl_token_123"
    assert cfg.gemini_api_key == "AIzaSyTest"
    assert cfg.midtrans_is_production is True
    assert cfg.has_gemini is True
    assert cfg.has_vercel is True
    assert cfg.has_midtrans is True
    assert cfg.has_email is True


def test_get_config_singleton():
    """Verify that get_config returns a singleton instance."""
    cfg1 = get_config()
    cfg2 = get_config()
    assert cfg1 is cfg2
