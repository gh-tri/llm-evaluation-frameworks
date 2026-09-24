"""
Real, live LangSmith-ecosystem calls behind framework/app.py's LangSmith
page, via `openevals` - the LangChain team's own library for building the
custom evaluator functions LangSmith's `evaluate()` runs.

Two live demos:

  #1 Define a metric  -> create_llm_as_judge with a criteria sentence
     folded into a plain prompt template ({inputs}/{outputs} placeholders,
     .format()-style rather than mustache). The closest LangSmith analog
     to G-Eval/AspectCritic/GEval/LLMClassifier - continuous 0-1 scoring
     with reasoning.

  #2 Pairwise comparison, live -> the same create_llm_as_judge, but asked
     to compare two candidate answers head to head rather than score one
     in isolation. This is a genuinely different judging shape from every
     other demo on this page (and every other framework's page) - LangSmith's
     ecosystem leans on pairwise/comparative evals as a first-class citizen
     (`evaluate_comparative`), not just pointwise scoring - which is why
     this page earns a second live demo.

Needs no LangSmith account for either - the evaluator function calls the
judge model directly. Just OPENAI_API_KEY.
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
class LiveJudgeResult:
    ok: bool
    score: Optional[float] = None
    reason: Optional[str] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


@dataclass
class LivePairwiseResult:
    ok: bool
    a_preferred: Optional[bool] = None
    reason: Optional[str] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def _pointwise_prompt(criteria: str) -> str:
    return (
        "You are grading an AI assistant's response to a customer.\n\n"
        "Question: {inputs}\n"
        "Response: {outputs}\n\n"
        f"Criteria: {criteria}\n\n"
        "Score the response from 0 to 1 against this criteria."
    )


def build_judge_snippet(name: str, criteria: str, model: str) -> str:
    prompt = _pointwise_prompt(criteria)
    return (
        "from openevals import create_llm_as_judge\n\n"
        "evaluator = create_llm_as_judge(\n"
        f"    prompt={prompt!r},\n"
        f"    feedback_key={name!r},\n"
        f"    model={('openai:' + model)!r},\n"
        "    continuous=True,\n"
        "    use_reasoning=True,\n"
        ")\n"
        "result = evaluator(inputs=<question>, outputs=<candidate answer>)\n"
        "result['score'], result['comment']  # -> what's shown below"
    )


def run_judge(
    name: str,
    criteria: str,
    input_text: str,
    actual_output: str,
    model: str = JUDGE_MODEL_DEFAULT,
) -> LiveJudgeResult:
    snippet = build_judge_snippet(name, criteria, model)

    status = check_openai()
    if not status.present:
        return LiveJudgeResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make a real "
                "judge-model call. Add one to .env and rerun."
            ),
            code_snippet=snippet,
        )

    try:
        from openevals import create_llm_as_judge

        evaluator = create_llm_as_judge(
            prompt=_pointwise_prompt(criteria),
            feedback_key=name,
            model=f"openai:{model}",
            continuous=True,
            use_reasoning=True,
        )

        start = time.monotonic()
        result = evaluator(inputs=input_text, outputs=actual_output)
        elapsed = time.monotonic() - start

        return LiveJudgeResult(
            ok=True,
            score=float(result["score"]),
            reason=result.get("comment"),
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LiveJudgeResult(ok=False, error=str(exc), code_snippet=snippet)


def _pairwise_prompt() -> str:
    return (
        "You are comparing two candidate responses to the same customer question.\n\n"
        "Question: {inputs}\n\n"
        "Response A: {outputs}\n"
        "Response B: {reference_outputs}\n\n"
        "Is Response A the better response - does it more directly address the "
        "customer's problem with a concrete next step?"
    )


def build_pairwise_snippet(model: str) -> str:
    prompt = _pairwise_prompt()
    return (
        "from openevals import create_llm_as_judge\n\n"
        "evaluator = create_llm_as_judge(\n"
        f"    prompt={prompt!r},\n"
        "    feedback_key='response_a_preferred',\n"
        f"    model={('openai:' + model)!r},\n"
        "    continuous=False,  # boolean: is A the better response?\n"
        "    use_reasoning=True,\n"
        ")\n"
        "result = evaluator(inputs=<question>, outputs=<answer A>, reference_outputs=<answer B>)\n"
        "result['score'], result['comment']  # -> what's shown below"
    )


def run_pairwise(
    question: str,
    answer_a: str,
    answer_b: str,
    model: str = JUDGE_MODEL_DEFAULT,
) -> LivePairwiseResult:
    snippet = build_pairwise_snippet(model)

    status = check_openai()
    if not status.present:
        return LivePairwiseResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make a real "
                "judge-model call. Add one to .env and rerun."
            ),
            code_snippet=snippet,
        )

    try:
        from openevals import create_llm_as_judge

        evaluator = create_llm_as_judge(
            prompt=_pairwise_prompt(),
            feedback_key="response_a_preferred",
            model=f"openai:{model}",
            continuous=False,
            use_reasoning=True,
        )

        start = time.monotonic()
        result = evaluator(inputs=question, outputs=answer_a, reference_outputs=answer_b)
        elapsed = time.monotonic() - start

        return LivePairwiseResult(
            ok=True,
            a_preferred=bool(result["score"]),
            reason=result.get("comment"),
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LivePairwiseResult(ok=False, error=str(exc), code_snippet=snippet)
