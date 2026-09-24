"""
The real, live DeepEval call behind the "run it live" button in app.py.

No mocks, no pre-computed numbers. Typing a new criteria and clicking a
button in the UI makes a real API call to the judge model via DeepEval's
G-Eval metric. This is deliberately separate from adapters/real_deepeval.py
(which scores this project's own six stations in batch) - this one is
built for a single, ad-hoc, presenter-editable call, with a return shape
that always succeeds even when the underlying call fails, so a bad or
missing API key never crashes the Streamlit page - it just explains why.
"""
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
class LiveGEvalResult:
    ok: bool
    score: Optional[float] = None
    reason: Optional[str] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def build_code_snippet(name: str, criteria: str, model: str, has_expected: bool) -> str:
    """The literal code that run_geval() below is about to execute, rendered
    for display so the audience sees code and result together - the whole
    point of the "vibe-coding a metric live" moment."""
    params = "[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT"
    params += ", SingleTurnParams.EXPECTED_OUTPUT]" if has_expected else "]"
    return (
        "from deepeval.metrics import GEval\n"
        "from deepeval.test_case import LLMTestCase, SingleTurnParams\n\n"
        f"metric = GEval(\n"
        f"    name={name!r},\n"
        f"    criteria={criteria!r},\n"
        f"    evaluation_params={params},\n"
        f"    model={model!r},\n"
        f")\n"
        f"test_case = LLMTestCase(\n"
        f"    input=<your input text>,\n"
        f"    actual_output=<your candidate answer>,\n"
        + ("    expected_output=<your reference answer>,\n" if has_expected else "")
        + f")\n"
        f"metric.measure(test_case)\n"
        f"metric.score, metric.reason  # -> what's shown below"
    )


def run_geval(
    name: str,
    criteria: str,
    input_text: str,
    actual_output: str,
    expected_output: str = "",
    model: str = JUDGE_MODEL_DEFAULT,
) -> LiveGEvalResult:
    has_expected = bool(expected_output.strip())
    snippet = build_code_snippet(name, criteria, model, has_expected)

    status = check_openai()
    if not status.present:
        return LiveGEvalResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make a real "
                "judge-model call. Add one to .env and rerun - nothing about this demo "
                "works without a real key, on purpose: it's a real API call, not a "
                "canned result."
            ),
            code_snippet=snippet,
        )

    try:
        from deepeval.metrics import GEval
        from deepeval.test_case import LLMTestCase, SingleTurnParams

        params = [SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT]
        if has_expected:
            params.append(SingleTurnParams.EXPECTED_OUTPUT)

        metric = GEval(name=name, criteria=criteria, evaluation_params=params, model=model)
        test_case = LLMTestCase(
            input=input_text,
            actual_output=actual_output,
            expected_output=expected_output if has_expected else None,
        )

        start = time.monotonic()
        metric.measure(test_case)
        elapsed = time.monotonic() - start

        return LiveGEvalResult(
            ok=True,
            score=round(float(metric.score), 3),
            reason=metric.reason,
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - this is a live, presenter-facing demo;
        # any failure (rate limit, timeout, bad key, malformed criteria) should show
        # up as a clear message on stage, never a crashed Streamlit page.
        return LiveGEvalResult(ok=False, error=str(exc), code_snippet=snippet)
