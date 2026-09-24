"""
Real, live Ragas calls behind framework/app.py's Ragas page.

Two live demos, deliberately mirroring DeepEval's page:

  #1 Define a metric  -> AspectCritic, Ragas's own plain-English,
     custom-criteria metric - the closest analog to DeepEval's G-Eval. Give
     it a name + a one-sentence definition, get back a binary (0/1) verdict
     on any (question, answer) pair. Unlike G-Eval, it returns a verdict
     only - no free-text reason - which is worth being upfront about on
     screen rather than hiding.

  #2 The RAG taxonomy, live -> Context Precision (Retrieval), Faithfulness
     (Generation), and Answer Correctness (End-to-end) run together on one
     small RAG example. This is Ragas's own three-bucket taxonomy for RAG
     metrics (see frontend/app.py:RAG_METRIC_CATEGORIES) - proven live with
     a real, grounded-vs-hallucinated contrast, rather than just described.

Matches this project's own adapters/real_ragas.py exactly: same
LangchainLLMWrapper/LangchainEmbeddingsWrapper construction, same
SingleTurnSample field names (user_input/response/retrieved_contexts/
reference), and the same AnswerCorrectness + answer_similarity= wiring -
get this wrong and construction still succeeds, but scoring raises
"AssertionError: AnswerSimilarity must be set" the moment it actually
runs. This project hit that exact bug once already; it's fixed here the
same way real_ragas.py fixes it, by building SemanticSimilarity first and
passing it in explicitly.
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
class LiveAspectCriticResult:
    ok: bool
    score: Optional[float] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


@dataclass
class LiveTaxonomyResult:
    ok: bool
    context_precision: Optional[float] = None
    faithfulness: Optional[float] = None
    answer_correctness: Optional[float] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def build_aspect_critic_snippet(name: str, definition: str, model: str) -> str:
    return (
        "from ragas.metrics import AspectCritic\n"
        "from ragas.llms import LangchainLLMWrapper\n"
        "from langchain_openai import ChatOpenAI\n"
        "from ragas import SingleTurnSample\n\n"
        f"llm = LangchainLLMWrapper(ChatOpenAI(model={model!r}, temperature=0))\n"
        f"metric = AspectCritic(name={name!r}, definition={definition!r}, llm=llm)\n\n"
        "sample = SingleTurnSample(user_input=<input>, response=<candidate answer>)\n"
        "metric.single_turn_score(sample)  # -> 0 or 1, no free-text reason"
    )


def run_aspect_critic(
    name: str,
    definition: str,
    input_text: str,
    actual_output: str,
    model: str = JUDGE_MODEL_DEFAULT,
) -> LiveAspectCriticResult:
    snippet = build_aspect_critic_snippet(name, definition, model)

    status = check_openai()
    if not status.present:
        return LiveAspectCriticResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make a real "
                "judge-model call. Add one to .env and rerun."
            ),
            code_snippet=snippet,
        )

    try:
        from ragas.metrics import AspectCritic
        from ragas.llms import LangchainLLMWrapper
        from langchain_openai import ChatOpenAI
        from ragas import SingleTurnSample

        llm = LangchainLLMWrapper(ChatOpenAI(model=model, temperature=0))
        metric = AspectCritic(name=name, definition=definition, llm=llm)
        sample = SingleTurnSample(user_input=input_text, response=actual_output)

        start = time.monotonic()
        score = metric.single_turn_score(sample)
        elapsed = time.monotonic() - start

        return LiveAspectCriticResult(
            ok=True,
            score=float(score),
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LiveAspectCriticResult(ok=False, error=str(exc), code_snippet=snippet)


def build_taxonomy_snippet(model: str) -> str:
    return (
        "from ragas.metrics import ContextPrecision, Faithfulness, AnswerCorrectness, SemanticSimilarity\n"
        "from ragas.llms import LangchainLLMWrapper\n"
        "from ragas.embeddings import LangchainEmbeddingsWrapper\n"
        "from langchain_openai import ChatOpenAI, OpenAIEmbeddings\n"
        "from ragas import SingleTurnSample\n\n"
        f"llm = LangchainLLMWrapper(ChatOpenAI(model={model!r}, temperature=0))\n"
        "embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())\n"
        "semantic_similarity = SemanticSimilarity(embeddings=embeddings)\n\n"
        "context_precision = ContextPrecision(llm=llm)                       # Retrieval\n"
        "faithfulness = Faithfulness(llm=llm)                                # Generation\n"
        "answer_correctness = AnswerCorrectness(                             # End-to-end\n"
        "    llm=llm, embeddings=embeddings, answer_similarity=semantic_similarity,\n"
        ")\n\n"
        "sample = SingleTurnSample(\n"
        "    user_input=<question>, response=<candidate answer>,\n"
        "    retrieved_contexts=[<context chunks>], reference=<ground-truth answer>,\n"
        ")\n"
        "context_precision.single_turn_score(sample)   # never reads `response`\n"
        "faithfulness.single_turn_score(sample)        # never reads `reference`\n"
        "answer_correctness.single_turn_score(sample)  # reads both `response` and `reference`"
    )


def run_taxonomy(
    question: str,
    contexts,
    candidate_answer: str,
    reference_answer: str,
    model: str = JUDGE_MODEL_DEFAULT,
) -> LiveTaxonomyResult:
    snippet = build_taxonomy_snippet(model)

    status = check_openai()
    if not status.present:
        return LiveTaxonomyResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make real "
                "judge-model or embedding calls. Add one to .env and rerun."
            ),
            code_snippet=snippet,
        )

    try:
        from ragas.metrics import ContextPrecision, Faithfulness, AnswerCorrectness, SemanticSimilarity
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from ragas import SingleTurnSample

        llm = LangchainLLMWrapper(ChatOpenAI(model=model, temperature=0))
        embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
        semantic_similarity = SemanticSimilarity(embeddings=embeddings)

        context_precision = ContextPrecision(llm=llm)
        faithfulness = Faithfulness(llm=llm)
        answer_correctness = AnswerCorrectness(
            llm=llm, embeddings=embeddings, answer_similarity=semantic_similarity,
        )

        sample = SingleTurnSample(
            user_input=question, response=candidate_answer,
            retrieved_contexts=list(contexts), reference=reference_answer,
        )

        start = time.monotonic()
        cp_score = context_precision.single_turn_score(sample)
        f_score = faithfulness.single_turn_score(sample)
        ac_score = answer_correctness.single_turn_score(sample)
        elapsed = time.monotonic() - start

        return LiveTaxonomyResult(
            ok=True,
            context_precision=float(cp_score),
            faithfulness=float(f_score),
            answer_correctness=float(ac_score),
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LiveTaxonomyResult(ok=False, error=str(exc), code_snippet=snippet)
