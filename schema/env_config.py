"""
Central place that checks for API keys needed by the "real" (non-mock)
framework adapters and the observability tracing wrappers.

Nothing in this project requires any key to run. The six station runners and
all mock adapters work fully offline. This module is only imported by the
real_* adapters and the LangSmith/Langfuse tracing wrappers, and it never
raises on a missing key - it reports back a clear status so a runner can
skip that one adapter and keep going instead of crashing the whole station.
"""
import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


@dataclass
class KeyStatus:
    name: str
    present: bool
    hint: str


def check_openai() -> KeyStatus:
    present = bool(os.environ.get("OPENAI_API_KEY"))
    return KeyStatus(
        name="OPENAI_API_KEY",
        present=present,
        hint="Needed by real_ragas.py, real_deepeval.py, real_trulens.py "
             "(all three use an OpenAI model as the LLM judge by default). "
             "Set it in a .env file at the project root, or export it in "
             "your shell before running a station with --real.",
    )


def check_langsmith() -> KeyStatus:
    present = bool(os.environ.get("LANGSMITH_API_KEY"))
    return KeyStatus(
        name="LANGSMITH_API_KEY",
        present=present,
        hint="Needed only for the LangSmith tracing/observability demo.",
    )


def check_langfuse() -> KeyStatus:
    present = bool(
        os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")
    )
    return KeyStatus(
        name="LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY",
        present=present,
        hint="Needed only for the Langfuse tracing/observability demo.",
    )


def require_openai_or_skip(adapter_label: str) -> bool:
    """Print a one-line, friendly notice and return False if the key is
    missing, so a runner can `continue` past that adapter instead of
    crashing. Returns True when the key is present."""
    status = check_openai()
    if not status.present:
        print(
            f"[{adapter_label}] Skipped - no OPENAI_API_KEY set. {status.hint}"
        )
    return status.present

def require_langsmith_or_skip(label: str) -> bool:
    """Same pattern as require_openai_or_skip, for the LangSmith tracing demo."""
    status = check_langsmith()
    if not status.present:
        print(f"[{label}] Skipped - no LANGSMITH_API_KEY set. {status.hint}")
    return status.present


def require_langfuse_or_skip(label: str) -> bool:
    """Same pattern as require_openai_or_skip, for the Langfuse tracing demo."""
    status = check_langfuse()
    if not status.present:
        print(f"[{label}] Skipped - no LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY set. {status.hint}")
    return status.present
