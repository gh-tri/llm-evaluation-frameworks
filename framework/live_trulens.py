"""
Real, live TruLens calls behind framework/app.py's TruLens page.

Two live demos, deliberately mirroring the DeepEval and Ragas pages:

  #1 Define a metric  -> TruLens doesn't ship a dedicated "custom metric"
     class the way DeepEval has G-Eval or Ragas has AspectCritic. Its
     generic mechanism sits one layer lower: `generate_score_and_reasons`
     takes any system_prompt/user_prompt pair and returns a normalized
     0-1 score plus a reasons dict. Every one of TruLens's ~20 named
     feedback functions (helpfulness_with_cot_reasons, coherence_with_cot_
     reasons, ...) is a thin wrapper that fills in a *fixed* criteria
     sentence and calls this. This demo does exactly what those wrappers
     do, but with a criteria sentence *you* type - verified straight from
     TruLens's own source (`_langchain_evaluate_with_cot_reasons`) and
     built only from its public pieces: the `LANGCHAIN_PROMPT_TEMPLATE_
     WITH_COT_REASONS_SYSTEM` template plus `generate_score_and_reasons`.

  #2 The RAG Triad, live -> Groundedness, Context Relevance, and Answer
     Relevance, run together on one small RAG example. This is TruLens's
     own coined, marketed concept (it named and popularized the term "RAG
     Triad") - proven live with a real grounded-vs-hallucinated contrast.
     This mirrors adapters/real_trulens.py's own three calls exactly.
"""
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from schema.env_config import check_openai  # noqa: E402

JUDGE_MODEL_DEFAULT = "gpt-4o-mini"


@dataclass
class LiveCriteriaResult:
    ok: bool
    score: Optional[float] = None
    reason: Optional[str] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


@dataclass
class LiveTriadResult:
    ok: bool
    groundedness: Optional[float] = None
    groundedness_reason: Optional[str] = None
    context_relevance: Optional[float] = None
    context_relevance_reasons: List[str] = field(default_factory=list)
    answer_relevance: Optional[float] = None
    answer_relevance_reason: Optional[str] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def build_criteria_snippet(criteria: str, model: str) -> str:
    return (
        "from trulens.providers.openai import OpenAI as TruOpenAI\n"
        "from trulens.feedback import prompts as trulens_prompts\n\n"
        f"provider = TruOpenAI(model_engine={model!r})\n\n"
        "# This is the exact template every *_with_cot_reasons method fills in for you -\n"
        "# here, the criteria sentence is yours instead of a fixed one:\n"
        "system_prompt = trulens_prompts.LANGCHAIN_PROMPT_TEMPLATE_WITH_COT_REASONS_SYSTEM.format(\n"
        f"    criteria={criteria!r},\n"
        ")\n"
        "user_prompt = trulens_prompts.LANGCHAIN_PROMPT_TEMPLATE_USER.format(submission=<your text>)\n\n"
        "score, reasons = provider.generate_score_and_reasons(system_prompt, user_prompt)\n"
        "score, reasons['reason']  # -> what's shown below"
    )


def run_custom_criteria(
    criteria: str,
    input_text: str,
    actual_output: str,
    model: str = JUDGE_MODEL_DEFAULT,
) -> LiveCriteriaResult:
    snippet = build_criteria_snippet(criteria, model)

    status = check_openai()
    if not status.present:
        return LiveCriteriaResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make a real "
                "judge-model call. Add one to .env and rerun."
            ),
            code_snippet=snippet,
        )

    try:
        from trulens.providers.openai import OpenAI as TruOpenAI
        from trulens.feedback import prompts as trulens_prompts

        provider = TruOpenAI(model_engine=model)

        system_prompt = trulens_prompts.LANGCHAIN_PROMPT_TEMPLATE_WITH_COT_REASONS_SYSTEM.format(
            criteria=criteria,
        )
        submission = f"User's question:\n{input_text}\n\nAssistant's response:\n{actual_output}"
        user_prompt = trulens_prompts.LANGCHAIN_PROMPT_TEMPLATE_USER.format(submission=submission)

        start = time.monotonic()
        score, reasons = provider.generate_score_and_reasons(system_prompt, user_prompt)
        elapsed = time.monotonic() - start

        return LiveCriteriaResult(
            ok=True,
            score=float(score),
            reason=reasons.get("reason") if isinstance(reasons, dict) else None,
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LiveCriteriaResult(ok=False, error=str(exc), code_snippet=snippet)


def build_triad_snippet(model: str) -> str:
    return (
        "from trulens.providers.openai import OpenAI as TruOpenAI\n\n"
        f"provider = TruOpenAI(model_engine={model!r})\n\n"
        "groundedness, g_reasons = provider.groundedness_measure_with_cot_reasons(\n"
        "    source=<joined retrieved context>, statement=<candidate answer>,\n"
        ")\n"
        "context_relevance_scores = [\n"
        "    provider.context_relevance_with_cot_reasons(question=<question>, context=c)\n"
        "    for c in <context chunks>\n"
        "]\n"
        "answer_relevance, a_reasons = provider.relevance_with_cot_reasons(\n"
        "    prompt=<question>, response=<candidate answer>,\n"
        ")"
    )


def run_rag_triad(
    question: str,
    contexts,
    candidate_answer: str,
    model: str = JUDGE_MODEL_DEFAULT,
) -> LiveTriadResult:
    snippet = build_triad_snippet(model)

    status = check_openai()
    if not status.present:
        return LiveTriadResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make real "
                "judge-model calls. Add one to .env and rerun."
            ),
            code_snippet=snippet,
        )

    try:
        from trulens.providers.openai import OpenAI as TruOpenAI

        provider = TruOpenAI(model_engine=model)
        joined_context = "\n".join(contexts)

        start = time.monotonic()
        groundedness_score, g_reasons = provider.groundedness_measure_with_cot_reasons(
            source=joined_context, statement=candidate_answer,
        )
        context_relevance_pairs = [
            provider.context_relevance_with_cot_reasons(question=question, context=c)
            for c in contexts
        ]
        answer_relevance_score, a_reasons = provider.relevance_with_cot_reasons(
            prompt=question, response=candidate_answer,
        )
        elapsed = time.monotonic() - start

        cr_scores = [s for s, _ in context_relevance_pairs] or [0.0]
        cr_reasons = [
            (r.get("reason") if isinstance(r, dict) else str(r))
            for _, r in context_relevance_pairs
        ]

        return LiveTriadResult(
            ok=True,
            groundedness=float(groundedness_score),
            groundedness_reason=g_reasons.get("reason") if isinstance(g_reasons, dict) else None,
            context_relevance=float(sum(cr_scores) / len(cr_scores)),
            context_relevance_reasons=cr_reasons,
            answer_relevance=float(answer_relevance_score),
            answer_relevance_reason=a_reasons.get("reason") if isinstance(a_reasons, dict) else None,
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LiveTriadResult(ok=False, error=str(exc), code_snippet=snippet)
