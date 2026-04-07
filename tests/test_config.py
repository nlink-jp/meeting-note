"""Tests for meeting-note configuration."""

import pytest

from meeting_note.config import GeminiConfig, get_gemini_config


class TestGeminiConfig:
    def test_defaults(self) -> None:
        config = GeminiConfig(project="test-project")
        assert config.project == "test-project"
        assert config.location == "us-central1"
        assert config.model == "gemini-2.5-flash"

    def test_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MEETING_NOTE_PROJECT", "env-project")
        monkeypatch.setenv("MEETING_NOTE_LOCATION", "asia-northeast1")
        config = GeminiConfig()
        assert config.project == "env-project"
        assert config.location == "asia-northeast1"


class TestGetGeminiConfig:
    def test_missing_project_raises(self) -> None:
        with pytest.raises(ValueError, match="GCP project ID is required"):
            get_gemini_config()

    def test_override_filters_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MEETING_NOTE_PROJECT", "env-project")
        config = get_gemini_config(project="", location="")
        assert config.project == "env-project"

    def test_override_applies(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MEETING_NOTE_PROJECT", "env-project")
        config = get_gemini_config(project="cli-project")
        assert config.project == "cli-project"
