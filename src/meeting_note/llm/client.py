"""Gemini LLM client for meeting-note."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from google import genai
from google.genai import types

from nlk.jsonfix import extract as jsonfix_extract, JsonFixError

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
        # Validate JSON is well-formed before passing to pydantic.
        # Gemini may truncate output without setting finish_reason=MAX_TOKENS.
        try:
            json.loads(response)
        except json.JSONDecodeError as e:
            # Attempt repair with nlk/jsonfix
            logger.warning(
                "Gemini returned malformed JSON (%s), attempting repair... "
                "Response length: %d chars.",
                e,
                len(response),
            )
            try:
                response = jsonfix_extract(response)
                json.loads(response)  # verify repair succeeded
                logger.info("JSON repair successful.")
            except (JsonFixError, json.JSONDecodeError):
                raise ValueError(
                    f"Gemini returned truncated/invalid JSON that could not be repaired ({e}). "
                    f"Response length: {len(response)} chars. "
                    f"max_output_tokens={self._config.max_output_tokens}. "
                    "Try increasing MEETING_NOTE_MAX_OUTPUT_TOKENS or splitting the input."
                ) from e
        try:
            return schema.model_validate_json(response)
        except ValidationError:
            logger.debug("Raw LLM response (first 500 chars): %s", response[:500])
            raise

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

    def load_audio_part(self, file_path: str, *, mime_type: str) -> Any:
        """Load an audio file as an inline Part for multimodal prompts.

        Vertex AI does not support files.upload() (Developer API only).
        Audio data is sent inline via Part.from_bytes().
        """
        from pathlib import Path

        data = Path(file_path).read_bytes()
        logger.info(
            "Loaded audio file: %s (%d bytes, %s)",
            file_path,
            len(data),
            mime_type,
        )
        return types.Part.from_bytes(data=data, mime_type=mime_type)

    def _call_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        files: list[Any] | None = None,
        response_mime_type: str | None = None,
        response_schema: type[BaseModel] | None = None,
        max_retries: int = 5,
        base_delay: float = 5.0,
    ) -> str:
        """Call Gemini API with exponential backoff on rate limit errors."""
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2,
            max_output_tokens=self._config.max_output_tokens,
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
                text = response.text
                if not text:
                    # Diagnose why the model returned no text
                    finish_reason = None
                    try:
                        finish_reason = response.candidates[0].finish_reason
                    except Exception:
                        pass
                    raise ValueError(
                        f"Gemini returned an empty response (finish_reason={finish_reason}). "
                        "Possible causes: safety filter, content policy block, or quota issue."
                    )
                # Detect truncated response due to output token limit
                try:
                    finish_reason = response.candidates[0].finish_reason
                except Exception:
                    finish_reason = None
                if finish_reason and str(finish_reason).upper() in ("MAX_TOKENS", "FINISH_REASON_MAX_TOKENS"):
                    raise ValueError(
                        f"Gemini response was truncated (finish_reason={finish_reason}). "
                        f"The output exceeded max_output_tokens={self._config.max_output_tokens}. "
                        "Consider increasing MEETING_NOTE_MAX_OUTPUT_TOKENS or splitting the input."
                    )
                return text
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
