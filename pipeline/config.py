"""
Centralized configuration management for Website Updater Studio.
Strongly-typed dataclass wrapping environment variables and operational paths.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

try:
    import dotenv
    dotenv.load_dotenv()
except Exception:
    pass


@dataclass
class PipelineConfig:
    """Master configuration container for all pipeline services."""

    # Dedicated SMTP Email
    email_host: str = field(default_factory=lambda: os.environ.get("OUTREACH_EMAIL_HOST", "smtp.gmail.com").strip())
    email_port: int = field(default_factory=lambda: int(os.environ.get("OUTREACH_EMAIL_PORT", "587")))
    email_user: str = field(default_factory=lambda: os.environ.get("OUTREACH_EMAIL_USER", "").strip())
    email_password: str = field(default_factory=lambda: os.environ.get("OUTREACH_EMAIL_PASSWORD", "").strip())

    # Sender Brand Identity
    sender_name: str = field(default_factory=lambda: os.environ.get("OUTREACH_SENDER_NAME", "Studio Modernisasi Web").strip())
    sender_wa: str = field(default_factory=lambda: os.environ.get("OUTREACH_SENDER_WA", "+62 851-2801-3767").strip())

    # Vercel Deployer
    vercel_token: str = field(default_factory=lambda: os.environ.get("VERCEL_TOKEN", "").strip())

    # Midtrans Payment Gateway
    midtrans_server_key: str = field(default_factory=lambda: os.environ.get("MIDTRANS_SERVER_KEY", "").strip())
    midtrans_client_key: str = field(default_factory=lambda: os.environ.get("MIDTRANS_CLIENT_KEY", "").strip())
    midtrans_is_production: bool = field(default_factory=lambda: os.environ.get("MIDTRANS_IS_PRODUCTION", "false").lower() == "true")

    # Google Gemini AI
    gemini_api_key: str = field(default_factory=lambda: os.environ.get("GEMINI_API_KEY", "").strip())
    gemini_model: str = field(default_factory=lambda: os.environ.get("GEMINI_MODEL", "gemini-3.7-flash").strip())

    # Dashboard Server Security
    dashboard_token: str = field(default_factory=lambda: os.environ.get("DASHBOARD_TOKEN", "").strip())

    # Directory Paths
    base_dir: str = field(default_factory=lambda: os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    clients_dir: str = field(default_factory=lambda: os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "clients")))
    db_path: str = field(default_factory=lambda: os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "clients", "pipeline.db")))

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def has_vercel(self) -> bool:
        return bool(self.vercel_token)

    @property
    def has_midtrans(self) -> bool:
        return bool(self.midtrans_server_key)

    @property
    def has_email(self) -> bool:
        return bool(self.email_user and self.email_password)


# Singleton
_config_instance: Optional[PipelineConfig] = None


def get_config(reload: bool = False) -> PipelineConfig:
    global _config_instance
    if _config_instance is None or reload:
        if reload:
            try:
                import dotenv
                dotenv.load_dotenv(override=True)
            except Exception:
                pass
        _config_instance = PipelineConfig()
    return _config_instance
