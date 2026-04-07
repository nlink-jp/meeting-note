"""Configuration management for meeting-note."""

from zoneinfo import ZoneInfo

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class GeminiConfig(BaseSettings):
    """Gemini API configuration loaded from environment variables."""

    project: str = Field(default="", description="GCP project ID")
    location: str = Field(default="us-central1", description="GCP location")
    model: str = Field(default="gemini-2.5-flash", description="Gemini model name")
    timezone: str = Field(default="Asia/Tokyo", description="Timezone for display (IANA name)")

    model_config = {"env_prefix": "MEETING_NOTE_", "env_file": ".env", "extra": "ignore"}

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except (KeyError, Exception) as exc:
            raise ValueError(f"Invalid timezone: {v!r}. Use IANA names (e.g. 'Asia/Tokyo', 'UTC').") from exc
        return v


def get_gemini_config(**overrides: str) -> GeminiConfig:
    """Load config with CLI overrides. Empty strings are ignored."""
    filtered = {k: v for k, v in overrides.items() if v}
    config = GeminiConfig(**filtered)
    if not config.project:
        raise ValueError(
            "GCP project ID is required. Set MEETING_NOTE_PROJECT environment variable or pass --project."
        )
    return config
