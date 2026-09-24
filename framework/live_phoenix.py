"""
Real, live Arize Phoenix call behind framework/app.py's Phoenix page.

One live demo: phoenix.evals's create_classifier. This is the one
framework on this page whose custom-criteria mechanism is categorical by
design, not continuous - you define named labels (each mapped to a score
and a description) instead of a 0-1 rubric, and get a label + explanation
back, not just a number. That's a genuinely different shape from every
other "define a metric" demo here, which is why one demo is enough to
make Phoenix's case.

Needs no Phoenix account - phoenix.evals's LLM class talks to the model
provider directly. Just OPENAI_API_KEY.
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
    label: Optional[str] = None
    score: Optional[float] = None
    explanation: Optional[str] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def _build_template(criteria: str) -> str:
    return (
        "You are grading an AI assistant's response to a customer question.\n\n"
        "Question: {input}\n"
        "Response: {output}\n\n"
        f"Criteria: {criteria}\n\n"
        "Does the response meet this criteria?"
    )


def build_code_snippet(name: str, criteria: str, model: str) -> str:
    template = _build_template(criteria)
    return (
        "from phoenix.evals import create_classifier, LLM\n\n"
        f"llm = LLM(provider='openai', model={model!r})\n"
        f"classifier = create_classifier(\n"
        f"    name={name!r},\n"
        f"    prompt_template={template!r},\n"
        "    llm=llm,\n"
        "    choices={'meets_criteria': (1, '...'), 'fails_criteria': (0, '...')},\n"
        ")\n"
        "scores = classifier.evaluate({'input': <question>, 'output': <candidate answer>})\n"
        "scores[0].label, scores[0].score, scores[0].explanation  # -> what's shown below"
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
        from phoenix.evals import create_classifier, LLM

        llm = LLM(provider="openai", model=model)
        classifier = create_classifier(
            name=name,
            prompt_template=_build_template(criteria),
            llm=llm,
            choices={
                "meets_criteria": (1, "the response meets the stated criteria"),
                "fails_criteria": (0, "the response does not meet the stated criteria"),
            },
        )

        start = time.monotonic()
        scores = classifier.evaluate({"input": input_text, "output": actual_output})
        elapsed = time.monotonic() - start

        score = scores[0] if scores else None
        if score is None:
            return LiveClassifierResult(ok=False, error="No score returned.", code_snippet=snippet)

        return LiveClassifierResult(
            ok=True,
            label=score.label,
            score=float(score.score) if score.score is not None else None,
            explanation=score.explanation,
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LiveClassifierResult(ok=False, error=str(exc), code_snippet=snippet)
