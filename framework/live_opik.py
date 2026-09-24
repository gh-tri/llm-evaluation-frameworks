"""
Real, live Opik call behind framework/app.py's Opik page.

One live demo: Opik ships its own GEval class - genuinely named and shaped
like DeepEval's, right down to the "task_introduction" + "evaluation_
criteria" split. Unlike every other framework on this page, Opik's GEval
needs no platform account at all for scoring: `track=False` skips its
optional trace-logging entirely, so this demo runs on nothing but
OPENAI_API_KEY, same as DeepEval/Ragas/TruLens.

One real difference worth being upfront about: `.score()` takes only
`output` - there's no separate `input` field the way DeepEval's
LLMTestCase or Ragas's SingleTurnSample have, so the question gets folded
into `task_introduction` instead.
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
class LiveGEvalOpikResult:
    ok: bool
    score: Optional[float] = None
    reason: Optional[str] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def build_code_snippet(name: str, criteria: str, model: str, input_text: str) -> str:
    return (
        "from opik.evaluation.metrics import GEval\n\n"
        f"metric = GEval(\n"
        f"    name={name!r},\n"
        f"    task_introduction=\"You are grading an AI assistant's response to: {input_text!r}\",\n"
        f"    evaluation_criteria={criteria!r},\n"
        f"    model={model!r},\n"
        "    track=False,  # no Opik account needed - scoring only\n"
        ")\n"
        "result = metric.score(output=<candidate answer>)\n"
        "result.value, result.reason  # -> what's shown below"
    )


def run_geval(
    name: str,
    criteria: str,
    input_text: str,
    actual_output: str,
    model: str = JUDGE_MODEL_DEFAULT,
) -> LiveGEvalOpikResult:
    snippet = build_code_snippet(name, criteria, model, input_text)

    status = check_openai()
    if not status.present:
        return LiveGEvalOpikResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make a real "
                "judge-model call. Add one to .env and rerun."
            ),
            code_snippet=snippet,
        )

    try:
        from opik.evaluation.metrics import GEval

        metric = GEval(
            name=name,
            task_introduction=f"You are grading an AI assistant's response to: {input_text}",
            evaluation_criteria=criteria,
            model=model,
            track=False,
        )

        start = time.monotonic()
        result = metric.score(output=actual_output)
        elapsed = time.monotonic() - start

        return LiveGEvalOpikResult(
            ok=True,
            score=float(result.value),
            reason=result.reason,
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LiveGEvalOpikResult(ok=False, error=str(exc), code_snippet=snippet)
