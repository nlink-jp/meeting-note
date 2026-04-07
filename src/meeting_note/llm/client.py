"""Gemini LLM client for meeting-note."""

from __future__ import annotations

import logging
import time
from typing import Any, TypeVar

from pydantic import BaseModel

from google import genai
from google.genai import types

from meeting_note.config import GeminiConfig

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    """Wrapper around the google-genai SDK for Vertex AI Gemini."""

    def __init__(self, config: GeminiConfig) -> None:
        self._config = config
        self._client = genai.Client(
            vertexai=True,
            project=config.project,
            location=config.location,
        )

    def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
        *,
        files: list[Any] | None = None,
    ) -> T:
        """Send a prompt and parse the response into a Pydantic model.

        Uses Gemini's response_schema for guaranteed valid JSON output.
        """
        response = self._call_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            files=files,
            response_mime_type="application/json",
            response_schema=schema,
        )
        return schema.model_validate_json(response)

    def complete_text(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Send a prompt and return raw text response."""
        return self._call_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    def upload_file(self, file_path: str, *, mime_type: str = "") -> Any:
        """Upload a file for use in multimodal prompts."""
        return self._client.files.upload(
            file_path=file_path,
            config={"mime_type": mime_type} if mime_type else None,
        )

    def delete_file(self, file_ref: Any) -> None:
        """Delete an uploaded file from Gemini Files API."""
        try:
            self._client.files.delete(name=file_ref.name)
            logger.info("Deleted uploaded file: %s", file_ref.name)
        except Exception as e:
            logger.warning("Failed to delete uploaded file %s: %s", file_ref.name, e)

    def _call_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        files: list[Any] | None = None,
        response_mime_type: str | None = None,
        response_schema: type[BaseModel] | None = None,
        max_retries: int = 3,
        base_delay: float = 2.0,
    ) -> str:
        """Call Gemini API with exponential backoff on rate limit errors."""
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2,
        )
        if response_mime_type:
            config.response_mime_type = response_mime_type
        if response_schema:
            config.response_schema = response_schema

        contents: list[Any] = []
        if files:
            contents.extend(files)
        contents.append(user_prompt)

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                response = self._client.models.generate_content(
                    model=self._config.model,
                    contents=contents,
                    config=config,
                )
                return response.text or ""
            except Exception as e:
                error_str = str(e).lower()
                is_retryable = any(
                    keyword in error_str
                    for keyword in ("429", "resource_exhausted", "rate limit", "quota")
                )
                if not is_retryable or attempt == max_retries:
                    raise
                last_error = e
                delay = base_delay * (2**attempt)
                logger.warning(
                    "Gemini API rate limited (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1,
                    max_retries + 1,
                    delay,
                    e,
                )
                time.sleep(delay)

        raise last_error  # type: ignore[misc]
