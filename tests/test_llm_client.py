"""Tests for Gemini LLM client."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from meeting_note.config import GeminiConfig
from meeting_note.llm.client import GeminiClient


class SampleSchema(BaseModel):
    title: str
    count: int = 0


class TestCompleteStructured:
    @patch("meeting_note.llm.client.genai.Client")
    def test_parses_response(self, mock_client_cls: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = '{"title": "Test Meeting", "count": 5}'
        mock_response.candidates = [MagicMock(finish_reason="STOP")]
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        config = GeminiConfig(project="test-project")
        client = GeminiClient(config)
        result = client.complete_structured("system", "user", SampleSchema)

        assert result.title == "Test Meeting"
        assert result.count == 5

    @patch("meeting_note.llm.client.genai.Client")
    def test_repairs_truncated_json(self, mock_client_cls: MagicMock) -> None:
        """Repairable truncated JSON should be fixed by nlk/jsonfix."""
        # Missing closing brace — jsonfix can repair this
        mock_response = MagicMock()
        mock_response.text = '{"title": "Repaired Meeting", "count": 3'
        mock_response.candidates = [MagicMock(finish_reason="STOP")]
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        config = GeminiConfig(project="test-project")
        client = GeminiClient(config)
        result = client.complete_structured("system", "user", SampleSchema)

        assert result.title == "Repaired Meeting"
        assert result.count == 3

    @patch("meeting_note.llm.client.genai.Client")
    def test_raises_on_unrepairable_json(self, mock_client_cls: MagicMock) -> None:
        """Completely broken JSON that jsonfix cannot repair should raise."""
        mock_response = MagicMock()
        mock_response.text = "not json at all"
        mock_response.candidates = [MagicMock(finish_reason="STOP")]
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        config = GeminiConfig(project="test-project")
        client = GeminiClient(config)

        with pytest.raises(ValueError, match="could not be repaired"):
            client.complete_structured("system", "user", SampleSchema)

    @patch("meeting_note.llm.client.genai.Client")
    def test_passes_files(self, mock_client_cls: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = '{"title": "Test"}'
        mock_response.candidates = [MagicMock(finish_reason="STOP")]
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        config = GeminiConfig(project="test-project")
        client = GeminiClient(config)
        fake_file = MagicMock()
        client.complete_structured("system", "user", SampleSchema, files=[fake_file])

        call_args = mock_client_cls.return_value.models.generate_content.call_args
        contents = call_args.kwargs["contents"]
        assert fake_file in contents
        assert "user" in contents


class TestCallWithRetry:
    @patch("meeting_note.llm.client.genai.Client")
    def test_success_first_attempt(self, mock_client_cls: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_response.candidates = [MagicMock(finish_reason="STOP")]
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        config = GeminiConfig(project="test-project")
        client = GeminiClient(config)
        result = client.complete_text("system", "user")
        assert result == "ok"

    @patch("meeting_note.llm.client.time.sleep")
    @patch("meeting_note.llm.client.genai.Client")
    def test_retries_on_429(self, mock_client_cls: MagicMock, mock_sleep: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_response.candidates = [MagicMock(finish_reason="STOP")]
        mock_generate = mock_client_cls.return_value.models.generate_content
        mock_generate.side_effect = [
            Exception("429 Resource Exhausted"),
            mock_response,
        ]

        config = GeminiConfig(project="test-project")
        client = GeminiClient(config)
        result = client.complete_text("system", "user")

        assert result == "ok"
        assert mock_generate.call_count == 2
        mock_sleep.assert_called_once()

    @patch("meeting_note.llm.client.genai.Client")
    def test_raises_on_max_tokens_truncation(self, mock_client_cls: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = '{"title": "truncated...'
        mock_response.candidates = [MagicMock(finish_reason="MAX_TOKENS")]
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        config = GeminiConfig(project="test-project")
        client = GeminiClient(config)

        with pytest.raises(ValueError, match="truncated"):
            client.complete_text("system", "user")

    @patch("meeting_note.llm.client.genai.Client")
    def test_raises_non_retryable(self, mock_client_cls: MagicMock) -> None:
        mock_client_cls.return_value.models.generate_content.side_effect = Exception("Invalid request")

        config = GeminiConfig(project="test-project")
        client = GeminiClient(config)

        with pytest.raises(Exception, match="Invalid request"):
            client.complete_text("system", "user")

    @patch("meeting_note.llm.client.time.sleep")
    @patch("meeting_note.llm.client.genai.Client")
    def test_exhausted_retries(self, mock_client_cls: MagicMock, mock_sleep: MagicMock) -> None:
        mock_client_cls.return_value.models.generate_content.side_effect = Exception("429 rate limit")

        config = GeminiConfig(project="test-project")
        client = GeminiClient(config)

        with pytest.raises(Exception, match="429 rate limit"):
            client._call_with_retry("system", "user", max_retries=2, base_delay=0.01)

        assert mock_client_cls.return_value.models.generate_content.call_count == 3


class TestLoadAudioPart:
    @patch("meeting_note.llm.client.genai.Client")
    def test_load_audio_returns_part(self, mock_client_cls: MagicMock, tmp_path) -> None:
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"\x00" * 100)

        config = GeminiConfig(project="test-project")
        client = GeminiClient(config)
        part = client.load_audio_part(str(audio_file), mime_type="audio/mpeg")

        assert part is not None
        assert part.inline_data is not None
        assert part.inline_data.mime_type == "audio/mpeg"
        assert len(part.inline_data.data) == 100

    @patch("meeting_note.llm.client.genai.Client")
    def test_rejects_large_file(self, mock_client_cls: MagicMock, tmp_path) -> None:
        audio_file = tmp_path / "large.mp3"
        audio_file.write_bytes(b"\x00" * (16 * 1024 * 1024))  # 16 MB

        config = GeminiConfig(project="test-project")
        client = GeminiClient(config)

        with pytest.raises(ValueError, match="Audio file too large"):
            client.load_audio_part(str(audio_file), mime_type="audio/mpeg")
