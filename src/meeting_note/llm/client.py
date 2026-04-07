"""Gemini LLM client for meeting-note."""

from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types

from meeting_note.config import GeminiConfig


class GeminiClient:
    """Wrapper around the google-genai SDK for Vertex AI Gemini."""

    def __init__(self, config: GeminiConfig) -> None:
        self._config = config
        self._client = genai.Client(
            vertexai=True,
            project=config.project,
            location=config.location,
        )

    def generate(
        self,
        prompt: str,
        *,
        files: list[Any] | None = None,
        response_schema: type | None = None,
    ) -> str:
        """Send a prompt to Gemini and return the text response."""
        contents: list[Any] = []
        if files:
            contents.extend(files)
        contents.append(prompt)

        config = types.GenerateContentConfig(
            response_mime_type="application/json" if response_schema else "text/plain",
            response_schema=response_schema,
        )

        response = self._client.models.generate_content(
            model=self._config.model,
            contents=contents,
            config=config,
        )
        return response.text or ""

    def upload_file(self, file_path: str, *, mime_type: str = "") -> Any:
        """Upload a file for use in multimodal prompts."""
        return self._client.files.upload(file_path=file_path, config={"mime_type": mime_type} if mime_type else None)
