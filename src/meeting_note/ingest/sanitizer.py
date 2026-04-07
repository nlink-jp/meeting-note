"""Prompt injection detection and sanitization for LLM inputs.

All user-sourced text (transcripts, audio transcriptions) MUST be sanitized
before inclusion in LLM prompts.

## Nonce-tagged wrapping strategy

A naive approach wraps text in a fixed tag such as ``<user_data>``.
This is exploitable: an attacker who knows the tag name can embed
``</user_data>`` in their input to close the data block early,
then inject instructions outside it.

To counter this, ``sanitize_for_llm()`` generates a cryptographically random
nonce per preprocessing session and embeds it in the tag name:

    <user_data_3a7f2c1d>
    ...untrusted text...
    </user_data_3a7f2c1d>

The nonce is unknown at the time the attacker crafts the input, so they
cannot predict the closing tag. The same nonce must be referenced in the
LLM system prompt so the model knows which tags delimit user data.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Injection detection patterns
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"ignore\s+(?:(?:previous|all|above|prior)\s+)*instructions?", "Instruction override attempt"),
    (r"forget\s+(everything|all|previous|prior)", "Memory wipe attempt"),
    (r"you\s+are\s+now\s+", "Persona reassignment attempt"),
    (r"new\s+instructions?\s*:", "New instruction injection"),
    (r"system\s*:\s*", "System prompt injection marker"),
    (r"<\s*/?system\s*>", "XML system tag injection"),
    (r"<\s*/?instructions?\s*>", "XML instructions tag injection"),
    (r"\[INST\]", "Llama instruction marker"),
    (r"###\s*instruction", "Markdown instruction header injection"),
    (r"act\s+as\s+", "Role-play directive"),
    (r"roleplay\s+as", "Role-play directive"),
    (r"pretend\s+(you\s+are|to\s+be)", "Persona pretend directive"),
    (r"disregard\s+(previous|all|above|prior)", "Instruction disregard attempt"),
    (r"override\s+(previous|system|all)\s+(prompt|instructions?)?", "System override attempt"),
]

_COMPILED_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), description)
    for pattern, description in _INJECTION_PATTERNS
]


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class SanitizationResult:
    """Result of sanitizing text for LLM input."""

    text: str
    nonce: str
    has_risk: bool
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def generate_nonce() -> str:
    """Generate a cryptographically random nonce (16-char hex, 64 bits)."""
    return secrets.token_hex(8)


def detect_injection(text: str) -> list[str]:
    """Detect potential prompt injection patterns in text."""
    warnings = []
    for compiled_pattern, description in _COMPILED_PATTERNS:
        match = compiled_pattern.search(text)
        if match:
            warnings.append(f"{description}: matched '{match.group(0)}' at position {match.start()}")
    return warnings


def sanitize_for_llm(text: str, nonce: str | None = None) -> SanitizationResult:
    """Sanitize text for safe use in LLM prompts.

    Wraps text in a nonce-tagged block to prevent prompt injection:

        <user_data_{nonce}>
        {text}
        </user_data_{nonce}>
    """
    if nonce is None:
        nonce = generate_nonce()

    warnings = detect_injection(text)
    safe_text = f"<user_data_{nonce}>\n{text}\n</user_data_{nonce}>"

    return SanitizationResult(
        text=safe_text,
        nonce=nonce,
        has_risk=len(warnings) > 0,
        warnings=warnings,
    )


def build_data_tag(nonce: str) -> str:
    """Return the opening data tag for the given nonce."""
    return f"<user_data_{nonce}>"


def build_data_tag_close(nonce: str) -> str:
    """Return the closing data tag for the given nonce."""
    return f"</user_data_{nonce}>"
