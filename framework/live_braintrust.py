"""
Real, live Braintrust (autoevals) call behind framework/app.py's Braintrust
page.

One live demo: autoevals.LLMClassifier - the library Braintrust's own docs
point to for defining a custom scorer. Unlike G-Eval/AspectCritic/Opik's
GEval, it doesn't turn one plain-English sentence into a rubric for you -
you write the whole grading template yourself, with Y/N (or any label)
choices mapped to scores. This demo writes that template from the criteria
sentence, matching Braintrust's own documented pattern exactly.

Needs no Braintrust account either - autoevals is a standalone scoring
library, decoupled from the Braintrust platform. Just OPENAI_API_KEY.
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
class LiveClassifierResult:
    ok: bool
    score: Optional[float] = None
    choice: Optional[str] = None
    reason: Optional[str] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def _build_template(criteria: str) -> str:
    return (
        "You are assessing a submitted answer to a question.\n\n"
        "Question: {{input}}\n"
        "Submitted answer: {{output}}\n\n"
        f"Criteria: {criteria}\n\n"
        "Does the submission meet the criteria above? Answer Y for yes or N for no."
    )


def build_code_snippet(name: str, criteria: str, model: str) -> str:
    template = _build_template(criteria)
    return (
        "from autoevals import LLMClassifier\n\n"
        f"classifier = LLMClassifier(\n"
        f"    name={name!r},\n"
        f"    prompt_template={template!r},\n"
        "    choice_scores={'Y': 1, 'N': 0},\n"
        f"    model={model!r},\n"
        "    use_cot=True,\n"
        ")\n"
        "result = classifier(output=<candidate answer>, input=<question>)\n"
        "result.score, result.metadata['rationale']  # -> what's shown below"
    )


def run_classifier(
    name: str,
    criteria: str,
    input_text: str,
    actual_output: str,
    model: str = JUDGE_MODEL_DEFAULT,
) -> LiveClassifierResult:
    snippet = build_code_snippet(name, criteria, model)

    status = check_openai()
    if not status.present:
        return LiveClassifierResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make a real "
                "judge-model call. Add one to .env and rerun."
            ),
            code_snippet=snippet,
        )

    try:
        from autoevals import LLMClassifier

        classifier = LLMClassifier(
            name=name,
            prompt_template=_build_template(criteria),
            choice_scores={"Y": 1, "N": 0},
            model=model,
            use_cot=True,
        )

        start = time.monotonic()
        result = classifier(output=actual_output, input=input_text)
        elapsed = time.monotonic() - start

        metadata = result.metadata or {}
        return LiveClassifierResult(
            ok=True,
            score=float(result.score) if result.score is not None else None,
            choice=metadata.get("choice"),
            reason=metadata.get("rationale"),
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LiveClassifierResult(ok=False, error=str(exc), code_snippet=snippet)
