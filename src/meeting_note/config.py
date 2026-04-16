"""Configuration management for meeting-note."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource


def _load_toml(tool_name: str) -> dict[str, Any]:
    """Load TOML config from ~/.config/<tool_name>/config.toml if it exists."""
    path = Path.home() / ".config" / tool_name / "config.toml"
    if not path.is_file():
        return {}
    with path.open("rb") as f:
        data = tomllib.load(f)
    flat: dict[str, Any] = {}
    if "gcp" in data and isinstance(data["gcp"], dict):
        if "project" in data["gcp"]:
            flat["project"] = data["gcp"]["project"]
        if "location" in data["gcp"]:
            flat["location"] = data["gcp"]["location"]
    if "model" in data and isinstance(data["model"], dict):
        model_section = data["model"]
        if "name" in model_section:
            flat["model"] = model_section["name"]
        for k, v in model_section.items():
            if k != "name":
                flat[k] = v
    if "gcs" in data and isinstance(data["gcs"], dict):
        if "audio_bucket" in data["gcs"]:
            flat["gcs_audio_bucket"] = data["gcs"]["audio_bucket"]
    for k, v in data.items():
        if k not in ("gcp", "model", "gcs") and not isinstance(v, dict):
            flat[k] = v
    return flat


class GeminiConfig(BaseSettings):
    """Gemini API configuration loaded from config file and environment variables."""

    project: str = Field(default="", description="GCP project ID")
    location: str = Field(default="us-central1", description="GCP location")
    model: str = Field(default="gemini-2.5-flash", description="Gemini model name")
    max_output_tokens: int = Field(default=65536, description="Maximum output tokens for Gemini response")
    timezone: str = Field(default="Asia/Tokyo", description="Timezone for display (IANA name)")
    gcs_audio_bucket: str = Field(default="", description="GCS bucket for audio file upload (required for -a)")

    model_config = {"env_prefix": "MEETING_NOTE_", "env_file": ".env", "extra": "ignore"}

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Priority: init (CLI flags) > env vars > .env > config.toml > defaults."""
        from pydantic_settings import InitSettingsSource

        toml_data = _load_toml("meeting-note")
        toml_source = InitSettingsSource(settings_cls, init_kwargs=toml_data)
        return (init_settings, env_settings, dotenv_settings, toml_source, file_secret_settings)

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
