"""Optional sentence suggestions from an OpenAI-compatible local endpoint.

Default target is Ollama at http://localhost:11434/v1 (no API key, ever —
auth headers are intentionally never sent). If the endpoint is unreachable,
generation silently falls back to the offline cloze/definition prompts.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional, Sequence

from .models import Entry, Question

DEFAULT_ENDPOINT = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3.2"
TIMEOUT_SECONDS = 45

SYSTEM_PROMPT = (
    "You help students study vocabulary. For each word written by the user, "
    "reply with ONE short example sentence that clearly uses the word. "
    "Plain text only, no numbering, nothing except the sentence."
)


def endpoint_from_env() -> tuple[str, str]:
    endpoint = os.environ.get("VQB_ENDPOINT", DEFAULT_ENDPOINT).rstrip("/")
    model = os.environ.get("VQB_MODEL", DEFAULT_MODEL)
    return endpoint, model


def chat(
    endpoint: str,
    model: str,
    user_text: str,
    timeout: float = TIMEOUT_SECONDS,
) -> Optional[str]:
    """POST a chat completion; returns the first message string, or None."""
    url = f"{endpoint}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.4,
        "max_tokens": 120,
    }
    data = json.dumps(payload).encode("utf-8")
    # Note: deliberately no API-key/auth header of any kind. This works with
    # Ollama, LM Studio, llama.cpp server, and other key-free local servers.
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
        return None
    try:
        return body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        return None


def build_writing_questions(
    entries: Sequence[Entry],
    endpoint: str,
    model: str,
    limit: int = 3,
) -> tuple[list[Question], bool]:
    """LLM-flavored writing prompts; returns (questions, llm_was_available)."""
    questions: list[Question] = []
    llm_ok = False
    for entry in entries[: max(limit, 0)]:
        sentence = chat(endpoint, model, entry.word)
        if sentence:
            llm_ok = True
            hint = f"Model example: {sentence}"
        else:
            hint = (
                f"{entry.definition}"
                if entry.definition.strip()
                else "Offline mode: write your own sentence."
            )
        questions.append(
            Question(
                qtype="writing_llm",
                prompt=f"Write one original sentence using “{entry.word}”.",
                answer=sentence or "(Open-ended; see the study-words section.)",
                hint=hint,
                entry=entry,
                difficulty="hard",
            )
        )
    return questions, llm_ok


def probe(endpoint: str, model: str) -> bool:
    """Cheap reachability check used by the CLI's --probe flag."""
    return chat(endpoint, model, "peace", timeout=8) is not None
