"""
Framework deep-dive: a standalone, presentation-focused page, one framework
at a time. Separate on purpose from frontend/app.py, which is about this
project's own data - this page is about the TOOL itself: how it works, how
it integrates, when to reach for it, the full map of what it can do, and
one or two capabilities proven live in front of an audience with a real
API call behind every number on screen.

Every framework's page follows the same two-layer shape: a full capability
map (honest, text-only inventory of everything the framework does) plus a
narrow live proof (one or two capabilities that are the framework's real
differentiator, run for real). Demo #1 is "define a metric" on every page
- the same idea (a plain-English criteria becomes a working judge-model
metric), backed by each framework's own real mechanism underneath:
  DeepEval -> G-Eval            Ragas -> AspectCritic      TruLens -> generate_score_and_reasons
Demo #2 is framework-specific, chosen to show what's actually distinctive:
  DeepEval -> Synthesizer (invents test data from a one-line scenario)
  Ragas    -> the RAG taxonomy, 3 metrics at once (Retrieval/Generation/End-to-end)
  TruLens  -> the RAG Triad, live (Groundedness + Context Relevance + Answer Relevance)

Run with:  uv run streamlit run framework/app.py
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from framework.catalog import FRAMEWORK_CATALOG, STATUS_LABELS
from framework.samples import SAMPLES, DEFAULT_CRITERIA, RAG_SAMPLE
from framework.live_deepeval import run_geval, JUDGE_MODEL_DEFAULT
from framework.live_synth import run_synthesis
from framework.live_ragas import run_aspect_critic, run_taxonomy
from framework.live_trulens import run_custom_criteria, run_rag_triad
from framework.live_opik import run_geval as run_geval_opik
from framework.live_braintrust import run_classifier as run_classifier_braintrust
from framework.live_phoenix import run_classifier as run_classifier_phoenix
from framework.live_langsmith import run_judge as run_judge_langsmith, run_pairwise
from framework.live_langfuse import run_score_and_push, check_langfuse
from framework.live_promptfoo import run_eval as run_eval_promptfoo, check_promptfoo_cli
from framework.live_garak import run_probe, check_garak
from schema.env_config import check_openai

st.set_page_config(page_title="Framework Deep-Dive", page_icon="🔬", layout="wide")

framework_key = st.sidebar.selectbox(
    "Framework", list(FRAMEWORK_CATALOG.keys()), format_func=lambda k: FRAMEWORK_CATALOG[k]["name"]
)
profile = FRAMEWORK_CATALOG[framework_key]

st.title(profile["name"])
st.caption(profile["tagline"])
st.markdown(f"[{profile['links']['site']}]({profile['links']['site']})  ·  [docs]({profile['links']['docs']})")

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("#### How it works")
    st.markdown(profile["how_it_works"])
with col2:
    st.markdown("#### How to integrate it")
    st.markdown(profile["integration"])
with col3:
    st.markdown("#### When to use it")
    st.markdown(profile["when_to_use"])

st.divider()

col_up, col_down = st.columns(2)
with col_up:
    st.markdown("#### ✅ Impressive points")
    for title, detail in profile["impressive_points"]:
        with st.expander(title):
            st.markdown(detail)
with col_down:
    st.markdown("#### ⚠️ Pain points")
    for title, detail in profile["pain_points"]:
        with st.expander(title):
            st.markdown(detail)

st.divider()

# ---------------------------------------------------------------------------
# The capability map - the honest inventory of everything this framework
# does, not just the one or two pieces proven live below.
# ---------------------------------------------------------------------------
st.header("The full capability map")
n_live = sum(1 for c in profile["capability_map"] if c["status"] == "live")
st.markdown(
    f"{profile['name']} does a lot more than the live demos below can show in one "
    f"sitting - **{len(profile['capability_map'])} distinct capabilities**, by its own "
    f"docs. This is the honest map: every one of them, one line each, with **{n_live} "
    "proven live** further down this page and the rest marked as reference-only or "
    "just worth knowing exists. The point of a live demo is proof it actually works, "
    "not full coverage - that's what this map is for."
)

capability_groups = list(dict.fromkeys(c["group"] for c in profile["capability_map"]))
for group in capability_groups:
    rows = [c for c in profile["capability_map"] if c["group"] == group]
    df = pd.DataFrame([
        {"Capability": r["capability"], "What it does": r["description"],
         "Status": STATUS_LABELS[r["status"]]}
        for r in rows
    ])
    st.markdown(f"**{group}**")
    st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

key_status = check_openai()

# ---------------------------------------------------------------------------
# Live in our UI - #1: define a metric
#
# Same idea on every framework's page - a plain-English criteria becomes a
# working judge-model metric - dispatched to whichever real mechanism that
# framework actually offers underneath.
# ---------------------------------------------------------------------------
DEMO1_MECHANISM = {
    "deepeval": "G-Eval",
    "ragas": "AspectCritic",
    "trulens": "generate_score_and_reasons",
    "opik": "GEval",
    "braintrust": "LLMClassifier",
    "phoenix": "create_classifier",
    "langsmith": "create_llm_as_judge",
}

# Frameworks whose live demo is "write a plain-English criteria, get a metric
# back" - the shared shape below. Langfuse (no built-in judge at all),
# Promptfoo (generates AND grades in one CLI run - no separate output field),
# and Garak (attacks a model rather than grading a pre-written answer) don't
# fit this shape and get their own fully bespoke section further down instead.
FITS_METRIC_DEMO = set(DEMO1_MECHANISM.keys())
# Frameworks that earn a genuine second live demo, because one demo alone
# wouldn't show something real and distinctive about that framework.
HAS_SECOND_DEMO = {"deepeval", "ragas", "trulens", "langsmith"}

if framework_key in FITS_METRIC_DEMO:
    header = (f"Live in our UI - #1: define a metric ({DEMO1_MECHANISM[framework_key]})"
              if framework_key in HAS_SECOND_DEMO
              else f"Live in our UI: define a metric ({DEMO1_MECHANISM[framework_key]})")
    st.header(header)
    st.markdown(
        "This is a real API call, not a canned result. Change the criteria below - that's "
        "a metric being defined live - pick or edit an example, and click run. Every "
        "number on screen comes from the actual call this framework just made."
    )
    st.write("\U0001F7E2 OPENAI_API_KEY configured - ready for real calls" if key_status.present
             else "⚪ No OPENAI_API_KEY set - the buttons below will explain what's missing instead of crashing")

    st.markdown("##### 1. Define the metric")
    if framework_key == "trulens":
        metric_name = "Custom criteria"
        col_model = st.columns([1])[0]
    else:
        col_name, col_model = st.columns([2, 1])
        with col_name:
            metric_name = st.text_input("Metric name", value="Helpfulness")
    with col_model:
        model = st.selectbox("Judge model", ["gpt-4o-mini", "gpt-4o"], index=0,
                              help=f"Defaults to {JUDGE_MODEL_DEFAULT} for cost, same as this project's other real adapters.")
    criteria = st.text_area("Plain-English criteria - this is the whole metric",
                             value=DEFAULT_CRITERIA, height=80)
    if framework_key == "trulens":
        st.caption(
            "TruLens has no separate metric-name field - just a criteria sentence, "
            "folded into the same chain-of-thought template every *_with_cot_reasons "
            "function uses internally."
        )
    if framework_key == "ragas":
        st.caption("AspectCritic returns a binary 0/1 verdict, not a 0-1 score - and no free-text reason.")
    if framework_key == "braintrust":
        st.caption(
            "LLMClassifier returns a binary verdict from the choice_scores map you write "
            "yourself (here: Y=1, N=0) - with chain-of-thought reasoning by default."
        )
    if framework_key == "phoenix":
        st.caption(
            "create_classifier returns one of the labels you define, not a continuous 0-1 "
            "float - genuinely categorical output is Phoenix's own differentiator here."
        )

    st.markdown("##### 2. Pick or write an example")
    sample_choice = st.radio(
        "Example", ["good", "mediocre", "bad", "custom"],
        format_func=lambda k: "Write your own" if k == "custom" else SAMPLES[k]["label"],
        horizontal=True,
        key="demo1_sample_choice",
    )
    if sample_choice == "custom":
        input_text = st.text_area("Input", value=SAMPLES["good"]["input"], height=70)
        actual_output = st.text_area("Actual output (the candidate answer being graded)", value="", height=90)
        expected_output = st.text_area("Expected output (optional reference answer)", value="", height=70)
    else:
        sample = SAMPLES[sample_choice]
        input_text = st.text_area("Input", value=sample["input"], height=70)
        actual_output = st.text_area("Actual output (the candidate answer being graded)",
                                      value=sample["actual_output"], height=90)
        expected_output = st.text_area("Expected output (optional reference answer)",
                                        value=sample["expected_output"], height=70)

    def run_metric_demo(name, criteria_text, input_text, actual_output, expected_output, model):
        """Common (ok, score, score_is_binary, reason, latency, error, code) shape across
        every "define a metric" demo on this page - each framework's real API underneath
        looks meaningfully different, which is exactly the point of showing the generated
        code snippet alongside the result."""
        if framework_key == "deepeval":
            r = run_geval(name, criteria_text, input_text, actual_output, expected_output, model)
            return r.ok, r.score, False, r.reason, r.latency_seconds, r.error, r.code_snippet
        if framework_key == "ragas":
            r = run_aspect_critic(name, criteria_text, input_text, actual_output, model)
            return r.ok, r.score, True, None, r.latency_seconds, r.error, r.code_snippet
        if framework_key == "trulens":
            r = run_custom_criteria(criteria_text, input_text, actual_output, model)
            return r.ok, r.score, False, r.reason, r.latency_seconds, r.error, r.code_snippet
        if framework_key == "opik":
            r = run_geval_opik(name, criteria_text, input_text, actual_output, model)
            return r.ok, r.score, False, r.reason, r.latency_seconds, r.error, r.code_snippet
        if framework_key == "braintrust":
            r = run_classifier_braintrust(name, criteria_text, input_text, actual_output, model)
            reason = (f"Classifier chose {r.choice!r}. {r.reason}" if (r.reason and r.choice) else r.reason)
            return r.ok, r.score, True, reason, r.latency_seconds, r.error, r.code_snippet
        if framework_key == "phoenix":
            r = run_classifier_phoenix(name, criteria_text, input_text, actual_output, model)
            return r.ok, r.score, True, r.explanation, r.latency_seconds, r.error, r.code_snippet
        r = run_judge_langsmith(name, criteria_text, input_text, actual_output, model)  # langsmith
        return r.ok, r.score, False, r.reason, r.latency_seconds, r.error, r.code_snippet

    st.markdown("##### 3. Run it")
    run_col, compare_col = st.columns(2)
    run_single = run_col.button("Run this example live", type="primary", disabled=not key_status.present)
    run_compare = compare_col.button("Run Good vs Mediocre vs Bad, live", disabled=not key_status.present)

    if run_single:
        with st.spinner(f"Calling {model} as the judge..."):
            ok, score, is_binary, reason, latency, error, code = run_metric_demo(
                metric_name, criteria, input_text, actual_output, expected_output, model
            )
        if ok:
            m1, m2 = st.columns([1, 2])
            with m1:
                if is_binary:
                    st.metric(metric_name, "Pass" if score >= 0.5 else "Fail")
                    st.caption(f"raw score: {score:.1f} · {latency}s · judge: {model}")
                else:
                    st.metric(metric_name, f"{score:.2f}")
                    st.caption(f"{latency}s · judge: {model}")
            with m2:
                if reason:
                    st.markdown("**Why:**")
                    st.info(reason)
                else:
                    st.caption("This call returns a verdict only - no free-text reason ships with it.")
        else:
            st.warning(error)
        with st.expander("The exact code that just ran"):
            st.code(code, language="python")

    if run_compare:
        cols = st.columns(3)
        for col, key in zip(cols, ["good", "mediocre", "bad"]):
            sample = SAMPLES[key]
            with col:
                st.markdown(f"**{sample['label']}**")
                with st.spinner(f"Scoring \"{sample['label']}\"..."):
                    ok, score, is_binary, reason, latency, error, code = run_metric_demo(
                        metric_name, criteria, sample["input"], sample["actual_output"],
                        sample["expected_output"], model,
                    )
                if ok:
                    if is_binary:
                        st.metric(metric_name, "Pass" if score >= 0.5 else "Fail")
                    else:
                        st.metric(metric_name, f"{score:.2f}")
                    if reason:
                        st.caption(reason)
                else:
                    st.warning(error)

    st.divider()

# ---------------------------------------------------------------------------
# Live in our UI - #2 (or the only demo, for the three that don't fit the
# shared "define a metric" shape above): framework-specific.
# ---------------------------------------------------------------------------
if framework_key == "deepeval":
    st.header("Live in our UI - #2: generate test data from scratch")
    st.markdown(
        "No dataset here either - just a one-line description of a scenario. DeepEval's "
        "Synthesizer invents plausible input/expected_output pairs from that description "
        "alone, via a real call to the same judge model. This is the direct answer to "
        "\"do I need a curated dataset to make a framework look good\" - no, the framework "
        "can build its own."
    )

    st.markdown("##### 1. Describe the scenario - no examples needed")
    scenario = st.text_input(
        "Scenario", value="A customer support agent handling shipping and delivery issues for an online retailer."
    )
    task = st.text_input(
        "Task", value="Answer customer questions about their order status and resolve delivery problems."
    )
    input_format = st.text_input(
        "What should a generated input look like?",
        value="A short customer message describing a shipping or delivery problem.",
    )
    num_goldens = st.slider("How many test cases to generate", min_value=1, max_value=5, value=3)

    run_synth = st.button("Generate test cases live", type="primary", disabled=not key_status.present)

    if run_synth:
        with st.spinner(f"Calling {model} to invent {num_goldens} test case(s)..."):
            synth_result = run_synthesis(scenario, task, input_format, num_goldens, model)
        if synth_result.ok:
            st.caption(f"Generated in {synth_result.latency_seconds}s · judge: {model}")
            for i, golden in enumerate(synth_result.goldens, start=1):
                with st.container(border=True):
                    st.markdown(f"**Generated test case {i}**")
                    st.markdown(f"**Input:** {golden.input}")
                    st.markdown(f"**Expected output:** {golden.expected_output}")
            st.caption(
                "These didn't exist a few seconds ago - copy one into the \"Write your own\" "
                "example above to grade it with the metric you defined in demo #1."
            )
        else:
            st.warning(synth_result.error)
        with st.expander("The exact code that just ran"):
            st.code(synth_result.code_snippet, language="python")

elif framework_key == "ragas":
    st.header("Live in our UI - #2: the RAG taxonomy, 3 metrics at once")
    st.markdown(
        "One small RAG example, three metrics, each from a different bucket of Ragas's "
        "own taxonomy: **Context Precision** (Retrieval - never reads the answer), "
        "**Faithfulness** (Generation - never reads the reference), and **Answer "
        "Correctness** (End-to-end - reads both). Running all three on the same example "
        "at once is the taxonomy, proven rather than just described."
    )

    with st.expander("The RAG example", expanded=True):
        st.markdown(f"**Question:** {RAG_SAMPLE['question']}")
        for i, ctx in enumerate(RAG_SAMPLE["contexts"], start=1):
            st.markdown(f"**Retrieved context {i}:** {ctx}")
        st.markdown(f"**Reference (ground-truth) answer:** {RAG_SAMPLE['reference']}")

    st.markdown("##### 1. Pick or write the candidate answer")
    answer_choice = st.radio(
        "Candidate answer", ["grounded", "hallucinated", "custom"],
        format_func=lambda k: "Write your own" if k == "custom" else RAG_SAMPLE["answers"][k]["label"],
        horizontal=True,
        key="ragas_answer_choice",
    )
    if answer_choice == "custom":
        candidate_answer = st.text_area("Candidate answer", value="", height=90, key="ragas_custom_answer")
    else:
        candidate_answer = st.text_area(
            "Candidate answer", value=RAG_SAMPLE["answers"][answer_choice]["text"], height=90,
            key="ragas_answer_text",
        )

    st.markdown("##### 2. Run it")
    run_col2, compare_col2 = st.columns(2)
    run_taxonomy_single = run_col2.button("Run all three metrics live", type="primary",
                                           disabled=not key_status.present, key="ragas_run_single")
    run_taxonomy_compare = compare_col2.button("Compare grounded vs hallucinated, live",
                                                disabled=not key_status.present, key="ragas_run_compare")

    if run_taxonomy_single:
        with st.spinner(f"Calling {model} for all three metrics..."):
            result = run_taxonomy(RAG_SAMPLE["question"], RAG_SAMPLE["contexts"], candidate_answer,
                                   RAG_SAMPLE["reference"], model)
        if result.ok:
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Context Precision (Retrieval)", f"{result.context_precision:.2f}")
            with m2:
                st.metric("Faithfulness (Generation)", f"{result.faithfulness:.2f}")
            with m3:
                st.metric("Answer Correctness (End-to-end)", f"{result.answer_correctness:.2f}")
            st.caption(f"{result.latency_seconds}s · judge: {model}")
        else:
            st.warning(result.error)
        with st.expander("The exact code that just ran"):
            st.code(result.code_snippet, language="python")

    if run_taxonomy_compare:
        rows = []
        for key in ["grounded", "hallucinated"]:
            answer_text = RAG_SAMPLE["answers"][key]["text"]
            with st.spinner(f"Scoring \"{RAG_SAMPLE['answers'][key]['label']}\"..."):
                result = run_taxonomy(RAG_SAMPLE["question"], RAG_SAMPLE["contexts"], answer_text,
                                       RAG_SAMPLE["reference"], model)
            if result.ok:
                rows.append({
                    "Answer": RAG_SAMPLE["answers"][key]["label"],
                    "Context Precision (Retrieval)": round(result.context_precision, 2),
                    "Faithfulness (Generation)": round(result.faithfulness, 2),
                    "Answer Correctness (End-to-end)": round(result.answer_correctness, 2),
                })
            else:
                st.warning(f"{RAG_SAMPLE['answers'][key]['label']}: {result.error}")
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption(
                "Context Precision barely moves - it never reads the answer. Faithfulness and "
                "Answer Correctness both drop on the hallucinated answer - that's the taxonomy "
                "doing its job."
            )

elif framework_key == "trulens":
    st.header("Live in our UI - #2: the RAG Triad, live")
    st.markdown(
        "One small RAG example, three feedback functions, TruLens's own coined trio: "
        "**Groundedness** (is the answer supported by the retrieved context), **Context "
        "Relevance** (is each retrieved chunk relevant to the question), and **Answer "
        "Relevance** (does the answer address the question). Run together, exactly as "
        "adapters/real_trulens.py already scores this project's own RAG station."
    )

    with st.expander("The RAG example", expanded=True):
        st.markdown(f"**Question:** {RAG_SAMPLE['question']}")
        for i, ctx in enumerate(RAG_SAMPLE["contexts"], start=1):
            st.markdown(f"**Retrieved context {i}:** {ctx}")

    st.markdown("##### 1. Pick or write the candidate answer")
    answer_choice_t = st.radio(
        "Candidate answer", ["grounded", "hallucinated", "custom"],
        format_func=lambda k: "Write your own" if k == "custom" else RAG_SAMPLE["answers"][k]["label"],
        horizontal=True,
        key="trulens_answer_choice",
    )
    if answer_choice_t == "custom":
        candidate_answer_t = st.text_area("Candidate answer", value="", height=90, key="trulens_custom_answer")
    else:
        candidate_answer_t = st.text_area(
            "Candidate answer", value=RAG_SAMPLE["answers"][answer_choice_t]["text"], height=90,
            key="trulens_answer_text",
        )

    st.markdown("##### 2. Run it")
    run_col3, compare_col3 = st.columns(2)
    run_triad_single = run_col3.button("Run the RAG Triad live", type="primary",
                                        disabled=not key_status.present, key="trulens_run_single")
    run_triad_compare = compare_col3.button("Compare grounded vs hallucinated, live",
                                             disabled=not key_status.present, key="trulens_run_compare")

    if run_triad_single:
        with st.spinner(f"Calling {model} for the RAG Triad..."):
            result = run_rag_triad(RAG_SAMPLE["question"], RAG_SAMPLE["contexts"], candidate_answer_t, model)
        if result.ok:
            t1, t2, t3 = st.columns(3)
            with t1:
                st.metric("Groundedness", f"{result.groundedness:.2f}")
                if result.groundedness_reason:
                    with st.expander("Why"):
                        st.info(result.groundedness_reason)
            with t2:
                st.metric("Context Relevance (avg)", f"{result.context_relevance:.2f}")
                if result.context_relevance_reasons:
                    with st.expander("Why"):
                        for i, r in enumerate(result.context_relevance_reasons, start=1):
                            st.info(f"Context {i}: {r}")
            with t3:
                st.metric("Answer Relevance", f"{result.answer_relevance:.2f}")
                if result.answer_relevance_reason:
                    with st.expander("Why"):
                        st.info(result.answer_relevance_reason)
            st.caption(f"{result.latency_seconds}s · judge: {model}")
        else:
            st.warning(result.error)
        with st.expander("The exact code that just ran"):
            st.code(result.code_snippet, language="python")

    if run_triad_compare:
        rows_t = []
        for key in ["grounded", "hallucinated"]:
            answer_text = RAG_SAMPLE["answers"][key]["text"]
            with st.spinner(f"Scoring \"{RAG_SAMPLE['answers'][key]['label']}\"..."):
                result = run_rag_triad(RAG_SAMPLE["question"], RAG_SAMPLE["contexts"], answer_text, model)
            if result.ok:
                rows_t.append({
                    "Answer": RAG_SAMPLE["answers"][key]["label"],
                    "Groundedness": round(result.groundedness, 2),
                    "Context Relevance": round(result.context_relevance, 2),
                    "Answer Relevance": round(result.answer_relevance, 2),
                })
            else:
                st.warning(f"{RAG_SAMPLE['answers'][key]['label']}: {result.error}")
        if rows_t:
            st.dataframe(pd.DataFrame(rows_t), use_container_width=True, hide_index=True)
            st.caption(
                "Groundedness is the one that should move the most - the hallucinated answer "
                "adds a claim (\"$20 store credit\") the retrieved context never mentions."
            )

elif framework_key == "langsmith":
    st.header("Live in our UI - #2: pairwise comparison, live")
    st.markdown(
        "Every other demo on this page scores one answer in isolation. This one asks a "
        "different question entirely - given the same question, which of two candidate "
        "answers is better? LangSmith's own ecosystem treats pairwise/comparative "
        "evaluation as a first-class citizen (`evaluate_comparative`), not an afterthought "
        "- which is why this framework earns a second live demo."
    )

    st.markdown("##### 1. Pick two candidate answers to compare")
    question_p = st.text_area("Question", value=SAMPLES["good"]["input"], height=70, key="ls_question")
    col_a, col_b = st.columns(2)
    with col_a:
        answer_a = st.text_area("Response A", value=SAMPLES["good"]["actual_output"], height=110, key="ls_answer_a")
    with col_b:
        answer_b = st.text_area("Response B", value=SAMPLES["bad"]["actual_output"], height=110, key="ls_answer_b")

    st.markdown("##### 2. Run it")
    run_pairwise_btn = st.button("Compare A vs B, live", type="primary",
                                  disabled=not key_status.present, key="ls_run_pairwise")
    if run_pairwise_btn:
        with st.spinner(f"Calling {model} to judge the pair..."):
            result = run_pairwise(question_p, answer_a, answer_b, model)
        if result.ok:
            st.metric("Response A preferred?", "Yes" if result.a_preferred else "No")
            if result.reason:
                st.markdown("**Why:**")
                st.info(result.reason)
            st.caption(f"{result.latency_seconds}s · judge: {model}")
        else:
            st.warning(result.error)
        with st.expander("The exact code that just ran"):
            st.code(result.code_snippet, language="python")

elif framework_key == "langfuse":
    st.header("Live in our UI: score an answer, then push it to a real trace")
    st.markdown(
        "Langfuse ships no judge of its own - \"no built-in judges of its own, you push "
        "scores in\" is the whole point of this row. So there's no separate \"define a "
        "metric\" demo to show here the way there is for every other framework on this "
        "page. This demo does the two things Langfuse actually asks of you: grade the "
        "answer yourself (one plain OpenAI call, no framework judge involved - that's the "
        "honest point), then push the resulting score into a real Langfuse trace via "
        "`create_score()`, and hand back the real trace URL Langfuse just created."
    )
    langfuse_status = check_langfuse()
    st.write("\U0001F7E2 OPENAI_API_KEY configured - ready for real calls" if key_status.present
             else "⚪ No OPENAI_API_KEY set - the button below will explain what's missing instead of crashing")
    st.write(("\U0001F7E2 LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY configured - ready to push a real trace")
             if langfuse_status.present
             else "⚪ No Langfuse credentials set - " + langfuse_status.hint)

    model_lf = st.selectbox("Judge model", ["gpt-4o-mini", "gpt-4o"], index=0, key="lf_model")
    criteria_lf = st.text_area("Plain-English criteria for the OpenAI call we write ourselves",
                                value=DEFAULT_CRITERIA, height=80, key="lf_criteria")

    st.markdown("##### Pick or write an example")
    sample_choice_lf = st.radio(
        "Example", ["good", "mediocre", "bad", "custom"],
        format_func=lambda k: "Write your own" if k == "custom" else SAMPLES[k]["label"],
        horizontal=True, key="lf_sample_choice",
    )
    if sample_choice_lf == "custom":
        input_text_lf = st.text_area("Input", value=SAMPLES["good"]["input"], height=70, key="lf_input")
        actual_output_lf = st.text_area("Actual output", value="", height=90, key="lf_output")
    else:
        sample_lf = SAMPLES[sample_choice_lf]
        input_text_lf = st.text_area("Input", value=sample_lf["input"], height=70, key="lf_input")
        actual_output_lf = st.text_area("Actual output", value=sample_lf["actual_output"], height=90, key="lf_output")

    run_lf = st.button("Score it and push to Langfuse, live", type="primary",
                        disabled=not (key_status.present and langfuse_status.present), key="lf_run")
    if run_lf:
        with st.spinner(f"Scoring with {model_lf}, then pushing to Langfuse..."):
            result = run_score_and_push(criteria_lf, input_text_lf, actual_output_lf, model_lf)
        if result.ok:
            m1, m2 = st.columns([1, 2])
            with m1:
                st.metric("Helpfulness", f"{result.score:.2f}")
                st.caption(f"{result.latency_seconds}s · judge: {model_lf}")
            with m2:
                if result.reason:
                    st.markdown("**Why:**")
                    st.info(result.reason)
            if result.trace_url:
                st.success(f"Pushed to a real Langfuse trace: {result.trace_url}")
        else:
            st.warning(result.error)
        with st.expander("The exact code that just ran"):
            st.code(result.code_snippet, language="python")

elif framework_key == "promptfoo":
    st.header("Live in our UI: generate, then grade, in one command")
    st.markdown(
        "Every other demo on this page grades an answer you already typed. Promptfoo is "
        "different - it's a YAML-configured CLI, not a Python library, and it actually "
        "calls the provider to GENERATE the answer from your prompt template, then grades "
        "it with its own `llm-rubric` assertion (a plain-English criteria, Promptfoo's own "
        "G-Eval analog) - prompt, live generation, and grading in one real `promptfoo eval` "
        "run, shelled out to the actual CLI."
    )
    promptfoo_ok = check_promptfoo_cli()
    st.write("\U0001F7E2 OPENAI_API_KEY configured - ready for real calls" if key_status.present
             else "⚪ No OPENAI_API_KEY set - the button below will explain what's missing instead of crashing")
    st.write("\U0001F7E2 promptfoo CLI found on PATH" if promptfoo_ok
             else "⚪ promptfoo isn't on PATH in this environment - install with `npm install -g promptfoo`")

    model_pf = st.selectbox("Provider model", ["gpt-4o-mini", "gpt-4o"], index=0, key="pf_model")
    prompt_template_pf = st.text_area(
        "Prompt template ({{message}} is the variable below)",
        value="You are a helpful customer support agent. Respond to: {{message}}",
        height=80, key="pf_template",
    )
    variable_value_pf = st.text_area("Value for {{message}}", value=SAMPLES["good"]["input"],
                                      height=70, key="pf_variable")
    criteria_pf = st.text_area("llm-rubric criteria", value=DEFAULT_CRITERIA, height=80, key="pf_criteria")

    run_pf = st.button("Run promptfoo eval, live", type="primary",
                        disabled=not (key_status.present and promptfoo_ok), key="pf_run")
    if run_pf:
        with st.spinner(f"Shelling out to promptfoo eval with {model_pf}..."):
            result = run_eval_promptfoo(prompt_template_pf, variable_value_pf, criteria_pf, model_pf)
        if result.ok:
            st.markdown("**Generated output:**")
            st.info(result.generated_output or "(empty)")
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Rubric verdict", "Pass" if result.passed else "Fail")
            with m2:
                st.metric("Score", f"{result.score:.2f}" if result.score is not None else "-")
            if result.reason:
                st.markdown("**Why:**")
                st.info(result.reason)
            st.caption(f"{result.latency_seconds}s · provider: {model_pf}")
        else:
            st.warning(result.error)
        with st.expander("The exact code that just ran"):
            st.code(result.code_snippet, language="python")

elif framework_key == "garak":
    st.header("Live in our UI: red-team a real model, live")
    st.markdown(
        "The most different demo on this whole page. Garak isn't a scoring framework at "
        "all - it's a red-team scanner. There's no answer to grade here; Garak attacks a "
        "live model with adversarial prompts and checks whether the attack succeeded. This "
        "shells out to the real `garak` CLI and runs one small, safe probe - "
        "**goodside.WhoIsRiley** (6 prompts) paired with its real detector, "
        "**goodside.RileyIsnt** - checking whether the model confidently hallucinates false "
        "biographical facts about an obscure real person rather than admitting uncertainty."
    )
    garak_ok = check_garak()
    st.write("\U0001F7E2 OPENAI_API_KEY configured - ready for real calls" if key_status.present
             else "⚪ No OPENAI_API_KEY set - the button below will explain what's missing instead of crashing")
    st.write("\U0001F7E2 garak found" if garak_ok
             else "⚪ garak isn't installed in this environment - install with `pip install garak`")

    model_gk = st.selectbox("Model to attack", ["gpt-4o-mini", "gpt-4o"], index=0, key="gk_model")
    generations_gk = st.slider("Generations per prompt", min_value=1, max_value=3, value=1, key="gk_generations")

    run_gk = st.button("Run the probe live", type="primary",
                        disabled=not (key_status.present and garak_ok), key="gk_run")
    if run_gk:
        with st.spinner(f"Running goodside.WhoIsRiley against {model_gk} (this can take a minute)..."):
            result = run_probe(model_gk, generations_gk)
        if result.ok:
            st.metric("Passed (safe)", f"{result.passed}/{result.total}")
            st.caption(f"{result.latency_seconds}s · attacked model: {model_gk}")
            for i, ex in enumerate(result.examples, start=1):
                with st.container(border=True):
                    st.markdown(f"**Prompt {i}:** {ex.prompt}")
                    st.markdown(f"**Model said:** {ex.output}")
                    st.markdown(f"**Verdict:** {'✅ safe' if ex.passed else '⚠️ hallucinated'}")
        else:
            st.warning(result.error)
        with st.expander("The exact code that just ran"):
            st.code(result.code_snippet, language="python")
