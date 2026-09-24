"""
Real, live Langfuse call behind framework/app.py's Langfuse page.

This page's demo looks different on purpose. Langfuse has no built-in
judge of its own - "no built-in judges of its own, you push scores in" is
the whole point of this row in the original brainstorm table. So there is
no "define a metric, get a score back" moment to demo here the way there
is for every other framework on this page. Instead, this demo shows the
other half of the real workflow: we grade the answer ourselves with one
plain OpenAI call (no framework judge involved at all - that's the honest
point), then push the resulting score into a real Langfuse trace via
`create_score()`, and hand back the real trace URL Langfuse just created.

Needs a real Langfuse account: LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY,
checked separately from OPENAI_API_KEY (which is still needed for the
scoring half). `auth_check()` validates the Langfuse credentials up front,
since `create_score()`/`flush()` are fire-and-forget and don't raise
synchronously on a bad key.
"""
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from schema.env_config import check_openai  # noqa: E402

JUDGE_MODEL_DEFAULT = "gpt-4o-mini"


@dataclass
class LangfuseKeyStatus:
    present: bool
    hint: str = "Needs LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY (see .env.example)."


def check_langfuse() -> LangfuseKeyStatus:
    present = bool(os.environ.get("LANGFUSE_PUBLIC_KEY")) and bool(os.environ.get("LANGFUSE_SECRET_KEY"))
    return LangfuseKeyStatus(present=present)


@dataclass
class LivePushResult:
    ok: bool
    score: Optional[float] = None
    reason: Optional[str] = None
    trace_url: Optional[str] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def build_code_snippet(criteria: str, model: str) -> str:
    return (
        "from openai import OpenAI\n"
        "from langfuse import Langfuse\n\n"
        "# Langfuse ships no judge of its own - the scoring below is a plain OpenAI\n"
        "# call we wrote ourselves, not anything Langfuse provides:\n"
        f"client = OpenAI()\n"
        f"resp = client.chat.completions.create(model={model!r}, messages=[\n"
        f"    {{'role': 'user', 'content': 'Criteria: {criteria}\\n\\n...score 0-1, then a reason'}}\n"
        "])\n"
        "score, reason = <parsed from resp>\n\n"
        "lf = Langfuse()\n"
        "trace_id = lf.create_trace_id()\n"
        "lf.create_score(trace_id=trace_id, name='Helpfulness', value=score, comment=reason)\n"
        "lf.flush()\n"
        "lf.get_trace_url(trace_id=trace_id)  # -> the real trace this demo just created"
    )


def run_score_and_push(
    criteria: str,
    input_text: str,
    actual_output: str,
    model: str = JUDGE_MODEL_DEFAULT,
) -> LivePushResult:
    snippet = build_code_snippet(criteria, model)

    openai_status = check_openai()
    if not openai_status.present:
        return LivePushResult(
            ok=False,
            error="No OPENAI_API_KEY set, so this can't score the answer in the first place.",
            code_snippet=snippet,
        )

    langfuse_status = check_langfuse()
    if not langfuse_status.present:
        return LivePushResult(
            ok=False,
            error=(
                "No LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY set, so this can't push a real "
                "score into a Langfuse project. Add both to .env and rerun - the scoring "
                "half above would still run today, but there's nowhere to push the result."
            ),
            code_snippet=snippet,
        )

    try:
        from openai import OpenAI
        from langfuse import Langfuse

        client = OpenAI()
        judge_prompt = (
            "You are grading an AI assistant's response to a customer question.\n\n"
            f"Question: {input_text}\n"
            f"Response: {actual_output}\n\n"
            f"Criteria: {criteria}\n\n"
            "Respond with exactly two lines: the first line a single number from 0 to 1 "
            "(the score), the second line a one-sentence reason."
        )

        start = time.monotonic()
        completion = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": judge_prompt}], temperature=0,
        )
        text = completion.choices[0].message.content.strip()
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        score = float(lines[0]) if lines else 0.0
        reason = lines[1] if len(lines) > 1 else text

        lf = Langfuse()
        lf.auth_check()  # raises cleanly on bad credentials, unlike create_score/flush
        trace_id = lf.create_trace_id()
        lf.create_score(trace_id=trace_id, name="Helpfulness", value=score, comment=reason,
                         data_type="NUMERIC")
        lf.flush()
        trace_url = lf.get_trace_url(trace_id=trace_id)
        elapsed = time.monotonic() - start

        return LivePushResult(
            ok=True,
            score=score,
            reason=reason,
            trace_url=trace_url,
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LivePushResult(ok=False, error=str(exc), code_snippet=snippet)
