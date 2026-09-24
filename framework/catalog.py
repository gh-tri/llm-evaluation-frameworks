"""
Framework profiles: the actual written content for the "framework" deep-dive
app. One dict per framework. Starting with DeepEval; the shape here is meant
to be copy-able for the next framework (Ragas, TruLens, LangSmith, ...)
rather than a one-off.

Every field is prose or a list of (title, detail) pairs - no scores, no
data. This file is pure content, same spirit as frontend/metric_glossary.py
and frontend/app.py's TOOLING_LANDSCAPE: keep the writing separate from the
rendering so either can change independently.

CAPABILITY_MAP exists because a mature framework is much bigger than any
one live demo can show - DeepEval's own docs list 17 distinct capabilities.
This is the honest inventory: every capability gets one line and a status,
so a reader sees the whole shape of the framework before landing on the
one or two pieces this page actually proves live. Building all 17 live
would be unreadable and mostly redundant with the docs; building only one
and staying silent about the rest overstates what's been shown. This map
is the fix for both.
"""

DEEPEVAL_PROFILE = {
    "name": "DeepEval",
    "tagline": "Open-source LLM evaluation, built to feel like pytest for your model's outputs.",
    "links": {
        "site": "https://deepeval.com",
        "docs": "https://deepeval.com/docs",
    },
    "how_it_works": (
        "DeepEval treats evaluation like unit testing for LLM outputs. You describe one "
        "interaction as an `LLMTestCase` - input, actual_output, and optionally "
        "expected_output, retrieval_context, or tools_called - pick or build a `Metric` "
        "object, and call `metric.measure(test_case)`. Every metric returns a 0-1 score "
        "plus a plain-English `reason` explaining why, even the objective-sounding ones: "
        "Faithfulness doesn't just say 0.4, it lists which specific claims in the answer "
        "weren't supported by the context.\n\n"
        "Two families of metrics sit side by side. About 50 pre-built, research-backed "
        "metrics cover the common cases - Faithfulness, Answer Relevancy, Hallucination, "
        "Toxicity, Bias, and RAG/agent-specific ones (this project already uses two of "
        "them in `adapters/real_deepeval.py`). And G-Eval, a general-purpose LLM-as-judge "
        "metric, covers everything else: you write your own grading criteria in plain "
        "English, and DeepEval turns it into a chain-of-thought scoring rubric "
        "automatically - no prompt engineering required. That's one of the two pieces "
        "this page lets you try live - the map below shows what else DeepEval does."
    ),
    "integration": (
        "Two lines to get started: `pip install deepeval`, then set `OPENAI_API_KEY` (or "
        "point it at another provider - DeepEval accepts any `DeepEvalBaseLLM`). From "
        "there it slots into a project three different ways:\n\n"
        "Called directly in your own code - exactly what this project already does in "
        "`adapters/real_deepeval.py`, where `metric.measure(test_case)` runs inline "
        "inside a station runner's loop and the score becomes one more row in the "
        "canonical store.\n\n"
        "As real pytest assertions - `assert_test(test_case, [metric])` lets "
        "`deepeval test run` become an actual CI command that fails a build on a quality "
        "regression, no custom scripting needed.\n\n"
        "Pushed to Confident AI - DeepEval's own hosted dashboard, entirely optional. "
        "This project deliberately skipped it in favor of the Streamlit UI you're looking "
        "at right now, but it exists if you want a shared UI without building one."
    ),
    "when_to_use": (
        "Reach for DeepEval when you want fast, code-first evaluation during development "
        "- especially when what you're grading is subjective (\"is this response too "
        "pushy\", \"does this match our brand voice\", \"did the agent actually solve the "
        "user's problem\") since G-Eval turns a criteria you can write in one sentence "
        "into a working metric in about three lines, with zero ML background needed.\n\n"
        "It's a weaker fit for anything that has to be fully deterministic (audit-grade, "
        "reproducible-to-the-decimal numbers) or for evaluating retrieval quality on its "
        "own without any generation step - that's better served by plain set-overlap math, "
        "which is exactly why this project's own retrieval_metrics.py (precision, recall, "
        "F1, MRR) stays deterministic and completely separate from the judge-based metrics."
    ),
    "impressive_points": [
        (
            "Define a metric in one sentence",
            "G-Eval takes a plain-English criteria string and writes and executes a full "
            "chain-of-thought grading rubric itself. No labeled training data, no prompt "
            "tuning - type a sentence, get a working metric.",
        ),
        (
            "Shows its work",
            "Every score ships with a `reason` string. A bad score is immediately "
            "explainable instead of a mystery number you have to go dig into.",
        ),
        (
            "Built for coding agents",
            "DeepEval explicitly markets support for defining and iterating on metrics "
            "through tools like Claude Code and Cursor - \"vibe-coding\" a metric into "
            "existence is a genuinely unusual thing for an eval framework to design "
            "around, and it's exactly how this page's live demos work.",
        ),
        (
            "A huge built-in catalog",
            "~50 pre-built metrics spanning RAG, agents, multimodal, and safety, so most "
            "common cases never need G-Eval at all - you reach for it specifically when "
            "nothing pre-built fits.",
        ),
        (
            "Doubles as a red-team tool",
            "DeepEval also ships a separate red-teaming module for probing jailbreaks and "
            "unsafe outputs - the same library that scores quality can also attack your "
            "own app.",
        ),
        (
            "Can invent its own test data",
            "The Synthesizer generates realistic test cases from nothing but a one-line "
            "description of your scenario - no hand-written dataset required, which is "
            "exactly what this page's second live demo shows.",
        ),
    ],
    "pain_points": [
        (
            "It's still a paid API call, every single time",
            "Every `metric.measure()` call is a real request to the judge model. Run it "
            "across a large dataset and both the bill and the latency add up fast - "
            "there's no free local mode for the judge-based metrics.",
        ),
        (
            "Nondeterministic by default",
            "Because scoring is LLM-based, the same input can drift slightly between runs "
            "unless you turn on strict_mode - which then collapses the nuanced 0-1 score "
            "down to a blunt pass/fail.",
        ),
        (
            "A slow or rate-limited judge call takes the whole metric down",
            "We hit this for real: in our own live run of this project's RAG station, "
            "DeepEval's judge call on one example (rag_007) hit a RetryError[TimeoutError] "
            "and failed outright. It's exactly why we added a try/except resilience "
            "wrapper around every adapter call in our station runners - one framework's "
            "flaky judge call should never take down an entire run's other results.",
        ),
        (
            "Quality depends on which judge model you pick",
            "A weak or cheap judge model (this project defaults to gpt-4o-mini for cost) "
            "gives noisier scores than a stronger one. There's a real quality/cost "
            "tradeoff baked into every G-Eval criteria you write, and it's easy to not "
            "notice until scores look inconsistent.",
        ),
        (
            "Your data goes through whichever API you point it at",
            "Unless you configure a self-hosted or on-prem model as the judge, every "
            "input/output pair being scored - or generated by the Synthesizer - is sent "
            "to OpenAI (or whichever provider) as part of the prompt.",
        ),
        (
            "Synthetic data still needs a human to check it",
            "The Synthesizer produces plausible-looking test cases fast, but \"plausible\" "
            "and \"correct\" aren't the same thing - a generated expected_output can be "
            "confidently wrong, so treat it as a first draft, not ground truth.",
        ),
    ],
    "capability_map": [
        {"group": "Scoring", "capability": "Metric Evaluation (G-Eval)",
         "description": "Score any output 0-1 against a plain-English criteria you write",
         "status": "live"},
        {"group": "Scoring", "capability": "Custom Classifiers",
         "description": "Define your own pass/fail behavioral, security, or format checks",
         "status": "mentioned"},

        {"group": "Test data", "capability": "Synthetic Data Generation (Synthesizer)",
         "description": "Generates test cases for you from a one-line scenario, no dataset needed",
         "status": "live"},
        {"group": "Test data", "capability": "Conversation Simulation",
         "description": "Generates multi-turn chatbot conversations at scale for testing",
         "status": "reference"},
        {"group": "Test data", "capability": "LLM Test Cases",
         "description": "The input/output/expected-output object every metric scores against",
         "status": "foundational"},

        {"group": "Agent & trace depth", "capability": "LLM Tracing",
         "description": "Auto-captures every span (retriever, tool call, planning step) of an agent run",
         "status": "reference"},
        {"group": "Agent & trace depth", "capability": "Component-Level Evals",
         "description": "Scores individual spans inside a trace separately, not just the final output",
         "status": "reference"},
        {"group": "Agent & trace depth", "capability": "Trajectory-Based Evals",
         "description": "Scores whether an agent completed its task and how it got there",
         "status": "reference"},
        {"group": "Agent & trace depth", "capability": "End-to-End Evals",
         "description": "Scores a full workflow from user input to final output",
         "status": "mentioned"},
        {"group": "Agent & trace depth", "capability": "Framework Integrations",
         "description": "Native hooks into LangChain, LangGraph, CrewAI, Pydantic AI, and others",
         "status": "mentioned"},

        {"group": "Workflow & ops", "capability": "CI/CD Integration",
         "description": "deepeval test run plugs straight into pytest - a bad score fails a build",
         "status": "mentioned"},
        {"group": "Workflow & ops", "capability": "Regression Testing",
         "description": "Compares two test runs side by side to catch a quality drop",
         "status": "mentioned"},
        {"group": "Workflow & ops", "capability": "Local Evaluation",
         "description": "Everything runs in your own environment; the cloud dashboard is opt-in",
         "status": "mentioned"},
        {"group": "Workflow & ops", "capability": "Online Production Evals",
         "description": "Live monitoring of production traces and conversations",
         "status": "reference"},
        {"group": "Workflow & ops", "capability": "Confident AI Cloud Platform",
         "description": "Hosted dashboard for shared results, team review, and production monitoring",
         "status": "reference"},

        {"group": "Extras", "capability": "Benchmarks",
         "description": "Runs your app against standardized LLM benchmarks (MMLU-style)",
         "status": "mentioned"},
        {"group": "Extras", "capability": "Prompt Optimization",
         "description": "Iteratively refines a prompt using eval feedback",
         "status": "mentioned"},
    ],
}

RAGAS_PROFILE = {
    "name": "Ragas",
    "tagline": "RAG evaluation built around one clear taxonomy: Retrieval, Generation, End-to-end.",
    "links": {
        "site": "https://ragas.io",
        "docs": "https://docs.ragas.io/en/stable/",
    },
    "how_it_works": (
        "Ragas scores one interaction at a time via a `SingleTurnSample` - `user_input`, "
        "`response`, and optionally `retrieved_contexts` and `reference` (a ground-truth "
        "answer). Each metric class is judge-model-driven, reads only the fields it "
        "actually needs, and returns `metric.single_turn_score(sample)`.\n\n"
        "The defining idea is the taxonomy: every metric sits in exactly one of three "
        "buckets, decided by which fields it reads. Retrieval-level metrics (Context "
        "Precision, Context Recall, Context Entity Recall) judge the retriever alone - "
        "contexts and, where needed, a reference - and never look at the generated "
        "answer. Generation-level metrics (Faithfulness, Answer Relevancy) judge the "
        "generator alone, reference-free. End-to-end metrics (Answer Correctness, Answer "
        "Semantic Similarity) compare the final answer directly against a labeled "
        "ground-truth reference, regardless of which stage produced it. This project's "
        "own comparison UI (see `frontend/app.py:RAG_METRIC_CATEGORIES`) uses this exact "
        "split - it's Ragas's own taxonomy, not a third-party guess.\n\n"
        "For anything a pre-built metric doesn't cover, `AspectCritic` (and its siblings "
        "`SimpleCriteriaScore`, `RubricsScore`) take a plain-English definition and return "
        "a judge-model verdict - Ragas's own analog to DeepEval's G-Eval, and the first "
        "live demo below."
    ),
    "integration": (
        "`pip install ragas`, then set `OPENAI_API_KEY` (or wrap any other provider - "
        "Ragas takes any `LangchainLLMWrapper` or `LlamaIndexLLMWrapper`). This project's "
        "`adapters/real_ragas.py` is the working example: build an LLM wrapper and an "
        "embeddings wrapper once, construct each metric with `llm=` (and `embeddings=` "
        "where needed), then call `.single_turn_score(sample)` per example inside a "
        "station runner's loop - the same lines this page's live demos run.\n\n"
        "Ragas also ships an async `aevaluate(dataset, metrics)` that scores a whole "
        "`EvaluationDataset` in parallel, with built-in progress bars and cost tracking. "
        "This project deliberately stays on the synchronous per-example path so scores "
        "can be attributed and displayed one row at a time in the Streamlit UI."
    ),
    "when_to_use": (
        "Reach for Ragas specifically when you need the Retrieval/Generation/End-to-end "
        "split - when a RAG pipeline's answer looks wrong and you need to know whether "
        "that's a retrieval problem or a generation problem before fixing the wrong "
        "stage. It's also the natural choice when you already have labeled ground-truth "
        "answers, since several of its most useful metrics (Context Precision, Answer "
        "Correctness) are reference-based rather than pure LLM-vibes scoring.\n\n"
        "It's a weaker fit when you have no ground truth at all and no interest in "
        "building any - `AspectCritic` covers that case, but DeepEval's G-Eval is a more "
        "mature, better-documented tool for open-ended, criteria-only grading, and "
        "Ragas's own synthetic test-set generator (`TestsetGenerator`) is a much heavier, "
        "network- and dependency-fragile pipeline than DeepEval's `Synthesizer` for the "
        "case where you have no data to start with at all."
    ),
    "impressive_points": [
        (
            "A named, opinionated taxonomy",
            "Retrieval / Generation / End-to-end isn't just documentation - it's baked "
            "into which fields each metric class actually reads, so the split is enforced "
            "by the API, not just a convention you have to remember.",
        ),
        (
            "Reference-based retrieval scoring",
            "Context Precision and Context Entity Recall judge the retriever against a "
            "ground-truth reference without ever looking at the generated answer - a "
            "genuinely different angle from DeepEval's and TruLens's reference-free "
            "retrieval metrics.",
        ),
        (
            "Async evaluation at dataset scale",
            "aevaluate() runs an entire EvaluationDataset in parallel with progress bars "
            "and per-run cost tracking built in, not bolted on.",
        ),
        (
            "Any LangChain- or LlamaIndex-wrapped model works",
            "LangchainLLMWrapper and LlamaIndexLLMWrapper mean the judge model is one "
            "constructor argument away from swapping providers entirely.",
        ),
        (
            "Plain-English criteria, three ways",
            "AspectCritic (binary), SimpleCriteriaScore (discrete scale), and "
            "RubricsScore (named rubric levels) cover three different shapes of "
            "\"define your own metric\", not just one.",
        ),
        (
            "An actual experiment-tracking mental model",
            "Ragas frames evaluation as tracking a metric over successive changes to a "
            "pipeline (an \"experiment\"), not just a one-off score - closer to how an ML "
            "team already thinks about iteration.",
        ),
    ],
    "pain_points": [
        (
            "AspectCritic gives a verdict, not a reason",
            "Unlike G-Eval or TruLens's chain-of-thought scoring, .single_turn_score() on "
            "AspectCritic returns a bare 0/1 float - confirmed straight from its own "
            "source, whose return type is just `float`. No free-text explanation ships "
            "with it, which is why this page's Ragas demo doesn't show a \"why\" panel.",
        ),
        (
            "AnswerCorrectness has a sharp-edged construction requirement",
            "We hit this for real: AnswerCorrectness(llm=, embeddings=) alone constructs "
            "without error, but the moment you call it, it raises \"AssertionError: "
            "AnswerSimilarity must be set\". It silently needs a SemanticSimilarity "
            "instance built first and passed in as answer_similarity= - a real bug this "
            "project's own real_ragas.py hit and had to fix.",
        ),
        (
            "TestsetGenerator is a genuinely heavy dependency",
            "Just importing ragas.testset.TestsetGenerator pulls in a tiktoken encoding "
            "download and a full knowledge-graph pipeline (embeddings, theme extraction, "
            "scenario generation) - much more fragile and slower to stand up than a quick "
            "live demo can afford, which is why this page's second demo stays with the "
            "metric taxonomy instead of mirroring DeepEval's synthetic-data angle.",
        ),
        (
            "Several metrics need embeddings, not just an LLM",
            "AnswerCorrectness and Answer Semantic Similarity both need an embeddings "
            "wrapper (OpenAIEmbeddings here) in addition to the judge LLM - one more "
            "moving part, and one more thing that silently needs an API key.",
        ),
        (
            "The taxonomy is a convention you have to already know",
            "Nothing in a metric's name tells you which bucket it's in - you either read "
            "the docs or the source's required_columns to find out, which is exactly why "
            "this project keeps its own RAG_METRIC_CATEGORY_MAP alongside Ragas rather "
            "than re-deriving it every time.",
        ),
        (
            "Judge-model cost and nondeterminism apply here too",
            "Same tradeoff as every LLM-as-judge framework: cheaper judge models are "
            "noisier, and every score is a real, billed API call - nothing here runs for "
            "free or byte-for-byte reproducibly.",
        ),
    ],
    "capability_map": [
        {"group": "Scoring", "capability": "Custom Metrics Framework",
         "description": "AspectCritic, SimpleCriteriaScore, RubricsScore - three ways to define a metric from a plain-English definition",
         "status": "live"},
        {"group": "Scoring", "capability": "Comprehensive Metric Taxonomy (30+ metrics)",
         "description": "Every metric sits in exactly one of Retrieval / Generation / End-to-end, enforced by which fields it reads",
         "status": "live"},
        {"group": "Scoring", "capability": "Multi-Turn Conversation Support",
         "description": "Scores a whole multi-turn conversation, not just one isolated input/output pair",
         "status": "mentioned"},

        {"group": "Test data", "capability": "Synthetic Test Set Generation",
         "description": "TestsetGenerator builds a knowledge graph from real documents and generates realistic test questions from it",
         "status": "reference"},
        {"group": "Test data", "capability": "Dataset Management",
         "description": "EvaluationDataset objects with built-in Hugging Face Hub upload/download for sharing test sets",
         "status": "mentioned"},

        {"group": "Workflow & ops", "capability": "Experiment-First Evaluation Pipeline",
         "description": "Frames evaluation as tracking a metric across successive pipeline changes, not a one-off score",
         "status": "reference"},
        {"group": "Workflow & ops", "capability": "Async Evaluation (aevaluate)",
         "description": "Scores an entire dataset in parallel with progress bars and built-in cost tracking",
         "status": "mentioned"},
        {"group": "Workflow & ops", "capability": "Cost Analysis Tools",
         "description": "Tracks token usage and estimated spend per evaluation run",
         "status": "mentioned"},

        {"group": "Extras", "capability": "Multi-Framework Integration",
         "description": "Native hooks for LangChain, LlamaIndex, and Haystack pipelines",
         "status": "mentioned"},
        {"group": "Extras", "capability": "LLM Provider Flexibility",
         "description": "LangchainLLMWrapper / LlamaIndexLLMWrapper make the judge model one constructor argument",
         "status": "foundational"},
        {"group": "Extras", "capability": "Language Adaptation",
         "description": "Metrics and prompts can adapt to evaluate non-English text",
         "status": "mentioned"},
    ],
}

TRULENS_PROFILE = {
    "name": "TruLens",
    "tagline": "Open-source LLM observability, built around traces, feedback functions, and the RAG Triad it coined.",
    "links": {
        "site": "https://www.trulens.org",
        "docs": "https://www.trulens.org/getting_started/",
    },
    "how_it_works": (
        "TruLens instruments your app to capture a trace - every span (a retriever call, "
        "a tool call, an LLM generation) as a recorded record - then scores that trace "
        "with feedback functions: small functions that call a judge model and return a "
        "normalized 0-1 score, optionally with a chain-of-thought reason attached.\n\n"
        "Most feedback functions ship pre-built with a fixed grading prompt - "
        "`helpfulness_with_cot_reasons`, `coherence_with_cot_reasons`, "
        "`groundedness_measure_with_cot_reasons`, and about twenty others, each on "
        "`trulens.providers.openai.OpenAI`. Underneath every one of them sits the same "
        "generic engine: `generate_score_and_reasons(system_prompt, user_prompt)`, which "
        "just sends whatever prompt it's given to the judge model and parses back a "
        "score and a reason. This project's own `adapters/real_trulens.py` already calls "
        "three of these pre-built functions directly - `groundedness_measure_with_cot_"
        "reasons`, `context_relevance_with_cot_reasons`, and `relevance_with_cot_reasons` "
        "- together known as the RAG Triad, TruLens's own coined term for exactly this "
        "trio."
    ),
    "integration": (
        "`pip install trulens trulens-providers-openai`, then set `OPENAI_API_KEY`. "
        "Construct a provider once - `TruOpenAI(model_engine=\"gpt-4o-mini\")` - and call "
        "its feedback methods directly, exactly as `adapters/real_trulens.py` does inside "
        "its `score_example()` loop; that's the lowest-ceremony path and what both of "
        "this page's live demos do.\n\n"
        "TruLens's fuller integration path wraps your app with `TruApp`/`TruChain`/"
        "`TruLlama` and a list of `Feedback(provider.some_method)` objects, which then "
        "auto-runs every feedback function against every recorded trace and pushes "
        "results into TruLens's own dashboard (`trulens.dashboard.run_dashboard()`) for "
        "browsing traces and comparing app versions side by side. This project skipped "
        "that dashboard in favor of driving the same provider calls straight into its "
        "own Streamlit UI."
    ),
    "when_to_use": (
        "Reach for TruLens when tracing and instrumentation matter as much as the score "
        "itself - it's the framework of the three here built around OpenTelemetry-native "
        "spans and a per-trace dashboard, so it fits agentic or multi-step pipelines "
        "where you need to see where in a trace a problem happened, not just get a "
        "single number back.\n\n"
        "It's a weaker fit when you want a purpose-built \"define a custom metric\" "
        "object like G-Eval or AspectCritic - TruLens has no such class. "
        "generate_score_and_reasons is fully generic but also fully manual: you write "
        "both the system prompt and the user prompt yourself (this page's first live "
        "demo builds them from TruLens's own public template strings, the same ones its "
        "pre-built functions use internally)."
    ),
    "impressive_points": [
        (
            "Coined the RAG Triad",
            "Groundedness / Context Relevance / Answer Relevance as a named, marketed "
            "trio isn't just a naming choice - it's genuinely a clean, minimal way to "
            "localize a RAG failure to one of three stages, and this page's second live "
            "demo runs all three together on one example.",
        ),
        (
            "OpenTelemetry-native tracing",
            "Traces are captured as real OTel spans, not a bespoke logging format, so "
            "they can flow into any OTel-compatible backend a team already has, not just "
            "TruLens's own dashboard.",
        ),
        (
            "Benchmarked judge accuracy",
            "TruLens publishes real benchmark numbers for its own judges (95% "
            "error-detection on TRAIL/GAIA-style agent benchmarks, 0.81 F1 on "
            "groundedness), rather than asking you to just trust an LLM-as-judge score "
            "at face value.",
        ),
        (
            "About twenty feedback functions out of the box",
            "Helpfulness, coherence, sentiment, harmfulness, moderation, tool selection, "
            "plan adherence, topic adherence, citation accuracy, and more - a genuinely "
            "broad pre-built library beyond just RAG.",
        ),
        (
            "The generic engine is exposed, not hidden",
            "generate_score_and_reasons is a real public method, not a private "
            "implementation detail - which is exactly what makes this page's "
            "custom-criteria demo possible without touching anything undocumented.",
        ),
        (
            "Agent-specific metrics beyond RAG",
            "tool_selection_with_cot_reasons, plan_adherence_with_cot_reasons, and "
            "agent_goal_accuracy_with_cot_reasons extend the same trace-and-score model "
            "to agentic workflows, not just single-turn RAG.",
        ),
    ],
    "pain_points": [
        (
            "No dedicated custom-metric object",
            "Unlike G-Eval or AspectCritic, there's no CustomMetric(criteria=...) class "
            "- defining your own criteria means building the system_prompt and "
            "user_prompt yourself from TruLens's own template strings, which this page's "
            "first live demo does explicitly rather than hiding it.",
        ),
        (
            "generate_score_and_reasons judges one blob of text, not an input/output pair",
            "Its user_prompt template takes a single SUBMISSION - there's no separate "
            "\"question\" field the way G-Eval's LLMTestCase or AspectCritic's "
            "SingleTurnSample have, so this page folds the question into the submission "
            "text itself.",
        ),
        (
            "A labeling mismatch is easy to make and hard to notice",
            "This project actually shipped context_relevancy mislabeled as "
            "context_precision at one point - two genuinely different concepts (an LLM "
            "judging one document's relevance vs. real set-overlap math against a "
            "labeled relevant-docs set) that TruLens's own naming doesn't do much to "
            "prevent confusing.",
        ),
        (
            "Groundedness pulls in NLTK's sentence tokenizer",
            "groundedness_measure_with_cot_reasons splits the source text into sentences "
            "with NLTK's punkt_tab tokenizer under the hood, which downloads its data "
            "file over the network the first time it's used - one more silent runtime "
            "dependency beyond the OpenAI call itself.",
        ),
        (
            "Structured-output parsing has several fallback layers",
            "generate_score_and_reasons tries a structured JSON response first, then "
            "falls back to parsing a \"Criteria: / Supporting Evidence: / Score:\" text "
            "block, and if that still doesn't parse cleanly, fires a second LLM call "
            "just to reformat the first response - resilient, but it means a single "
            "feedback call can silently become two.",
        ),
        (
            "Same judge-model cost and nondeterminism as the others",
            "Every feedback call is a real, billed request to the judge model, and "
            "scores can drift slightly between runs at temperature 0.0 like any "
            "LLM-as-judge system.",
        ),
    ],
    "capability_map": [
        {"group": "Scoring", "capability": "Feedback Functions & Metrics (20+)",
         "description": "Pre-built judge-model functions: helpfulness, coherence, sentiment, harmfulness, moderation, and more",
         "status": "mentioned"},
        {"group": "Scoring", "capability": "Domain Customization",
         "description": "generate_score_and_reasons plus TruLens's own prompt templates let you grade against any criteria you write",
         "status": "live"},
        {"group": "Scoring", "capability": "RAG Triad Metrics",
         "description": "Groundedness, Context Relevance, and Answer Relevance - TruLens's own coined trio for localizing a RAG failure",
         "status": "live"},
        {"group": "Scoring", "capability": "LLM-as-Judge Scoring",
         "description": "The generic scoring engine every named feedback function and this page's two demos are built on",
         "status": "foundational"},

        {"group": "Tracing & ops", "capability": "Tracing & Instrumentation",
         "description": "Auto-captures every span of an app run - retriever calls, tool calls, LLM generations - as a structured trace",
         "status": "mentioned"},
        {"group": "Tracing & ops", "capability": "OpenTelemetry Integration",
         "description": "Traces are real OTel spans, portable to any OTel-compatible backend",
         "status": "mentioned"},

        {"group": "Workflow & ops", "capability": "Batch & Live Evaluation",
         "description": "Feedback functions run over a batch of recorded traces or live against production traffic",
         "status": "mentioned"},
        {"group": "Workflow & ops", "capability": "Leaderboard & Comparison",
         "description": "Compares multiple app versions side by side on the same feedback functions",
         "status": "reference"},
        {"group": "Workflow & ops", "capability": "Dashboard Visualization",
         "description": "trulens.dashboard.run_dashboard() browses traces and scores in a hosted local UI",
         "status": "reference"},
    ],
}

STATUS_LABELS = {
    "live": "\U0001F7E2 Live demo",
    "reference": "⚪ Reference card",
    "mentioned": "· Mentioned",
    "foundational": "· Foundational (seen in the code above)",
}

from framework.catalog2 import (  # noqa: E402
    BRAINTRUST_PROFILE,
    PROMPTFOO_PROFILE,
    OPIK_PROFILE,
    LANGSMITH_PROFILE,
    PHOENIX_PROFILE,
    LANGFUSE_PROFILE,
    GARAK_PROFILE,
    GUARDRAILS_PROFILE,
)

FRAMEWORK_CATALOG = {
    "deepeval": DEEPEVAL_PROFILE,
    "ragas": RAGAS_PROFILE,
    "trulens": TRULENS_PROFILE,
    "opik": OPIK_PROFILE,
    "braintrust": BRAINTRUST_PROFILE,
    "phoenix": PHOENIX_PROFILE,
    "langsmith": LANGSMITH_PROFILE,
    "langfuse": LANGFUSE_PROFILE,
    "promptfoo": PROMPTFOO_PROFILE,
    "garak": GARAK_PROFILE,
    "guardrails": GUARDRAILS_PROFILE,
}
