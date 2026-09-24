"""
Continuation of catalog.py's per-framework profiles - Braintrust, Promptfoo,
Opik, LangSmith, Phoenix, Langfuse, Garak. Split into a second file only
because catalog.py was already large; FRAMEWORK_CATALOG in catalog.py
imports and merges these in. Same shape and rules as catalog.py's own
docstring: every field is prose or (title, detail) pairs, no data.
"""

BRAINTRUST_PROFILE = {
    "name": "Braintrust",
    "tagline": "An evals platform with autoevals as its standalone scoring library underneath.",
    "links": {
        "site": "https://www.braintrust.dev",
        "docs": "https://www.braintrust.dev/docs",
    },
    "how_it_works": (
        "Braintrust the platform logs experiments, prompts, and datasets; `autoevals` is "
        "the separate, standalone Python package that actually computes scores, and it's "
        "what this page uses. autoevals ships ~25 pre-built scorers (Factuality, "
        "AnswerRelevancy, Faithfulness, Battle for A/B prompt comparisons, and more), plus "
        "`LLMClassifier` for anything custom: you write a full grading prompt template "
        "with `{{output}}`/`{{input}}`/`{{expected}}` placeholders and a `choice_scores` "
        "map (e.g. `{\"Y\": 1, \"N\": 0}`), and it runs that template with chain-of-thought "
        "reasoning by default.\n\n"
        "That's the one real difference from G-Eval, AspectCritic, or Opik's GEval: none "
        "of those need you to write the actual grading prompt - a plain criteria sentence "
        "is enough and the framework builds the rubric. autoevals' `LLMClassifier` is "
        "explicit instead of automatic - more control, more to write."
    ),
    "integration": (
        "`pip install autoevals`, then set `OPENAI_API_KEY`. That's genuinely it for "
        "scoring - autoevals is decoupled from the Braintrust platform, confirmed by "
        "running `LLMClassifier` with no `BRAINTRUST_API_KEY` at all, same as this page's "
        "live demo does.\n\n"
        "Braintrust the platform layers on top when you want it: `braintrust eval` runs "
        "your scorers against a dataset and logs every result to a hosted experiment "
        "view, with side-by-side diffing between runs. This page skips that layer "
        "entirely, exactly like this project skips Confident AI and Langfuse's own "
        "hosted dashboards - the scorer is the reusable part."
    ),
    "when_to_use": (
        "Reach for autoevals when you want a large catalog of pre-built scorers "
        "(Factuality, Battle, Sql, Translation, and others cover a lot of common cases "
        "with zero setup) and don't mind writing an explicit grading template for the "
        "cases that catalog doesn't cover. It's a good fit if you're already comparing "
        "two outputs head to head (`Battle`) rather than just scoring one in isolation.\n\n"
        "It's a weaker fit than G-Eval or Opik's GEval when you want the fastest possible "
        "path from \"one sentence of criteria\" to \"a working metric\" - `LLMClassifier` "
        "asks you to write the whole prompt and the choice-to-score mapping yourself, "
        "which is more setup for the same basic idea."
    ),
    "impressive_points": [
        (
            "Decoupled from the platform entirely",
            "autoevals needs no Braintrust account for scoring - confirmed by running it "
            "with no BRAINTRUST_API_KEY set. The platform is genuinely optional.",
        ),
        (
            "A big catalog of pre-built scorers",
            "~25 ready-made scorers spanning factuality, SQL correctness, translation "
            "quality, and head-to-head comparison (Battle) - more breadth out of the box "
            "than most of the frameworks on this page.",
        ),
        (
            "Built for head-to-head comparison, not just scoring",
            "Battle is a first-class pre-built scorer for \"which of these two outputs is "
            "better\", the same idea this page's LangSmith page has to build manually.",
        ),
        (
            "CoT reasoning by default",
            "LLMClassifier runs with use_cot=True unless you turn it off - the rationale "
            "comes back in result.metadata alongside the score, not as an afterthought.",
        ),
    ],
    "pain_points": [
        (
            "No automatic rubric generation",
            "Unlike G-Eval or Opik's GEval, LLMClassifier doesn't turn a plain sentence "
            "into a rubric for you - you write the full prompt template and the choice-to-"
            "score mapping yourself, every time.",
        ),
        (
            "Two separate things share the Braintrust name",
            "\"Braintrust\" the hosted eval platform and `autoevals` the scoring library "
            "are separate installs with separate docs - easy to conflate when you're first "
            "looking at this ecosystem, since most tutorials assume you want both.",
        ),
        (
            "Template variables are mustache, not .format()",
            "prompt_template uses {{output}} / {{input}} / {{expected}} (chevron/mustache "
            "syntax) - a different templating convention from openevals' plain "
            "{inputs}/{outputs} .format()-style placeholders, easy to mix up if you're "
            "working across both in the same afternoon, as this page's build did.",
        ),
        (
            "Same judge-model cost and nondeterminism as the others",
            "Every LLMClassifier call is a real, billed request to the judge model, same "
            "tradeoffs as G-Eval, AspectCritic, or any other LLM-as-judge mechanism here.",
        ),
    ],
    "capability_map": [
        {"group": "Scoring", "capability": "Custom Classifiers (LLMClassifier)",
         "description": "Write a full grading template + choice-to-score map for any criteria",
         "status": "live"},
        {"group": "Scoring", "capability": "Built-in Scorer Library (~25)",
         "description": "Factuality, Sql, Translation, Battle (head-to-head), and more, zero setup",
         "status": "mentioned"},
        {"group": "Scoring", "capability": "Code-Based Scorers",
         "description": "Deterministic scorers (exact match, JSON diff, Levenshtein) alongside the LLM ones",
         "status": "mentioned"},

        {"group": "Platform", "capability": "Experiments & Trials",
         "description": "Runs a scorer across a dataset and logs results to a hosted, diffable experiment view",
         "status": "reference"},
        {"group": "Platform", "capability": "Human Review Queues",
         "description": "Routes low-confidence or flagged results to a person for manual grading",
         "status": "mentioned"},
        {"group": "Platform", "capability": "Playground",
         "description": "Compares prompts and models side by side in a hosted UI",
         "status": "mentioned"},
        {"group": "Platform", "capability": "Loop (prompt optimization)",
         "description": "Iteratively rewrites a prompt using eval feedback",
         "status": "mentioned"},

        {"group": "Ops", "capability": "Production Monitoring",
         "description": "Runs scorers against live production traffic, not just offline datasets",
         "status": "reference"},
        {"group": "Ops", "capability": "Dataset Management",
         "description": "Versioned datasets with diffing between versions",
         "status": "mentioned"},
    ],
}

PROMPTFOO_PROFILE = {
    "name": "Promptfoo",
    "tagline": "A YAML-configured CLI for testing prompts across models - not a Python library.",
    "links": {
        "site": "https://www.promptfoo.dev",
        "docs": "https://www.promptfoo.dev/docs/intro/",
    },
    "how_it_works": (
        "Promptfoo is a Node.js CLI, not something you `import`. You write a "
        "`promptfooconfig.yaml`: one or more prompt templates, one or more providers "
        "(any model, or several at once), a list of test cases with variables, and a "
        "list of assertions per test case. `promptfoo eval` then runs the full matrix - "
        "every prompt against every provider against every test case - generating each "
        "response for real and grading it in the same pass.\n\n"
        "For custom criteria, the `llm-rubric` assertion type is Promptfoo's own "
        "G-Eval-style plain-English judge: `type: llm-rubric, value: \"<your criteria>\"` "
        "is the whole definition, graded by an LLM judge automatically. Deterministic "
        "assertions (`contains`, `equals`, `javascript`, `python`) sit right alongside it "
        "in the same test case, so a rubric-graded criteria and a hard string check can "
        "cover the same output side by side."
    ),
    "integration": (
        "`npm install -g promptfoo` (Node.js, not pip), then `promptfoo eval -c "
        "promptfooconfig.yaml`. This page's live demo does exactly that from Python: it "
        "writes a temp YAML file and shells out to the real `promptfoo` binary via "
        "`subprocess.run(...)`, then parses the JSON it writes back out with `-o "
        "results.json` - there's no Python import path into Promptfoo at all, which is "
        "why this page's demo looks different from every other framework here.\n\n"
        "In a real pipeline, `promptfoo eval` is the thing you'd wire into CI directly - "
        "it exits non-zero on a failed assertion, so a GitHub Action can fail a build on "
        "a prompt regression without any custom scripting."
    ),
    "when_to_use": (
        "Reach for Promptfoo specifically when the question is about the PROMPT or the "
        "PROVIDER, not a pre-written answer - comparing three prompt variants across two "
        "models on the same ten test cases is one YAML file and one command, with a "
        "results matrix built in. It's also a natural fit for teams that don't want a "
        "Python dependency at all, since it's a standalone binary.\n\n"
        "It's a weaker fit when your team already has a Python evaluation pipeline and "
        "wants to grade already-generated outputs in-process - every other framework on "
        "this page does that with a function call; Promptfoo means writing YAML and "
        "shelling out, which is exactly what this page's live demo has to do."
    ),
    "impressive_points": [
        (
            "Prompt x provider x test-case matrix testing",
            "One config file runs every prompt variant against every provider against "
            "every test case in one command - genuinely different from the "
            "one-metric-on-one-example shape of every other framework here.",
        ),
        (
            "Generation and grading in one pass",
            "Nothing is pre-written: the provider generates the real answer from your "
            "prompt template, then llm-rubric grades it, in a single `promptfoo eval` run - "
            "the only demo on this page where the candidate answer doesn't already exist.",
        ),
        (
            "A real red-teaming mode built in",
            "`promptfoo redteam` generates and runs adversarial test cases against your "
            "app directly from the same config format, without a separate tool - a "
            "lighter-weight overlap with what Garak does as a dedicated scanner.",
        ),
        (
            "CI-native by design",
            "Non-zero exit codes on failed assertions and a documented GitHub Action make "
            "it a natural drop-in for a build pipeline, no custom wrapper needed.",
        ),
    ],
    "pain_points": [
        (
            "It's a CLI, not a library",
            "There's no Python (or JS) API to call in-process - integrating it into an "
            "existing app means shelling out and parsing JSON back, exactly what this "
            "page's live_promptfoo.py does.",
        ),
        (
            "Telemetry and version checks reach out by default",
            "A bare `promptfoo eval` also tries to phone home to update-check and "
            "telemetry endpoints unless you set PROMPTFOO_DISABLE_TELEMETRY and "
            "PROMPTFOO_DISABLE_UPDATE_CHECK - easy to miss in a sandboxed or "
            "network-restricted environment, where those calls just add failed "
            "connection attempts to every run.",
        ),
        (
            "Retry backoff can make a broken run look hung",
            "On a real provider failure, the underlying fetch client retries several "
            "times with backoff before giving up - a single eval run can take well over "
            "a minute to fail cleanly, worth knowing before you set a short timeout "
            "around it.",
        ),
        (
            "Same judge-model cost and nondeterminism as the others",
            "llm-rubric is still an LLM-as-judge call under the hood - same billing and "
            "score-drift tradeoffs as G-Eval or any other judge mechanism on this page.",
        ),
    ],
    "capability_map": [
        {"group": "Scoring", "capability": "llm-rubric Assertions",
         "description": "Plain-English criteria, graded by an LLM judge - Promptfoo's own G-Eval analog",
         "status": "live"},
        {"group": "Scoring", "capability": "Deterministic Assertions",
         "description": "contains, equals, javascript, python, regex checks alongside the LLM ones",
         "status": "mentioned"},
        {"group": "Scoring", "capability": "Model-Graded Comparisons",
         "description": "select-best and similar assertion types rank several outputs against each other",
         "status": "mentioned"},

        {"group": "Test data", "capability": "Dataset-Driven Test Cases",
         "description": "Test cases and variables loaded straight from CSV/YAML files",
         "status": "foundational"},
        {"group": "Test data", "capability": "Synthetic Test Generation",
         "description": "promptfoo generate produces new test cases from a config's existing prompts",
         "status": "mentioned"},

        {"group": "Workflow & ops", "capability": "Matrix Testing",
         "description": "Every prompt variant x every provider x every test case, in one run",
         "status": "mentioned"},
        {"group": "Workflow & ops", "capability": "Red Teaming",
         "description": "promptfoo redteam generates and runs adversarial test cases from the same config format",
         "status": "mentioned"},
        {"group": "Workflow & ops", "capability": "CI Integration",
         "description": "Non-zero exit on a failed assertion, with a documented GitHub Action",
         "status": "mentioned"},
        {"group": "Workflow & ops", "capability": "Result Caching",
         "description": "Caches identical prompt/provider calls between runs to cut cost during iteration",
         "status": "mentioned"},
        {"group": "Workflow & ops", "capability": "Web Viewer",
         "description": "promptfoo view opens a local browser UI over past eval results",
         "status": "reference"},
    ],
}

OPIK_PROFILE = {
    "name": "Opik",
    "tagline": "Comet's open-source LLM evaluation and observability library.",
    "links": {
        "site": "https://www.comet.com/site/products/opik/",
        "docs": "https://www.comet.com/docs/opik/",
    },
    "how_it_works": (
        "Opik ships its own `GEval` class - genuinely named and shaped like DeepEval's: "
        "give it a `task_introduction` and an `evaluation_criteria` string, call "
        "`metric.score(output=...)`, get back a `ScoreResult` with `.value` (0-1) and "
        "`.reason`. Alongside GEval sit ~30 pre-built metrics (Hallucination, Moderation, "
        "AnswerRelevance, ContextPrecision/Recall, and more), and `BaseMetric` for "
        "writing a fully custom metric class from scratch when even GEval's shape "
        "doesn't fit.\n\n"
        "One real difference from DeepEval's LLMTestCase: `GEval.score()` takes only "
        "`output` - there's no separate `input` field, so the question has to be folded "
        "into `task_introduction` instead, same constraint TruLens's generic engine has."
    ),
    "integration": (
        "`pip install opik`, then set `OPENAI_API_KEY`. The one thing worth knowing: "
        "`GEval(..., track=True)` is the default, and tracking pushes trace data to "
        "Opik's platform (self-hosted or Comet's cloud), which needs its own login. Pass "
        "`track=False` and scoring runs on nothing but the OpenAI key - confirmed by "
        "running exactly that with no OPIK_API_KEY set at all, which is what this page's "
        "live demo does.\n\n"
        "With tracking on, Opik's `@opik.track` decorator auto-instruments a function's "
        "calls into spans, and metrics can be attached to run automatically against "
        "logged traces - closer to TruLens's trace-first model than to DeepEval's "
        "call-it-inline model."
    ),
    "when_to_use": (
        "Reach for Opik when you want a DeepEval-shaped custom metric (GEval) but also "
        "want the option of full tracing and an open-source, self-hostable observability "
        "backend without a hard SaaS dependency - Comet's platform is available "
        "self-hosted, not just cloud-only.\n\n"
        "It's a weaker fit if you specifically want DeepEval's separate input/output "
        "fields on a test case, or DeepEval's much larger (~50) pre-built metric catalog "
        "and dedicated red-teaming module - Opik's metric library is smaller, and its "
        "GEval folds the question into one combined field instead of keeping it separate."
    ),
    "impressive_points": [
        (
            "A G-Eval-shaped metric with zero account needed",
            "track=False means Opik's own GEval scores with nothing but an OpenAI key - "
            "no Comet account, no Opik server, confirmed by running it that way directly.",
        ),
        (
            "Same category, different vendor, converging design",
            "Three separate companies (Confident AI, Comet, and implicitly OpenAI's own "
            "eval conventions) all landed on a near-identical \"plain criteria in, "
            "chain-of-thought score out\" shape - worth noting as a sign this pattern has "
            "become a genuine industry convention, not one vendor's invention.",
        ),
        (
            "Guardrails, not just after-the-fact scoring",
            "Opik also ships a guardrails module for validating output before it's "
            "returned to a user, not just grading it after the fact - a different point "
            "in the pipeline than every other framework on this page checks.",
        ),
        (
            "Open-source and self-hostable end to end",
            "The tracing/observability backend itself, not just the scoring library, can "
            "run entirely on infrastructure you control.",
        ),
    ],
    "pain_points": [
        (
            "Tracking is on by default",
            "GEval(track=True) is the default constructor value - leave it unset and "
            "every score call tries to log to Opik's backend, which needs credentials "
            "this demo deliberately avoids requiring.",
        ),
        (
            "No separate input field on GEval",
            "score(output=...) is the only argument - the question or context has to be "
            "folded into task_introduction as a string, which is a little more awkward "
            "than DeepEval's LLMTestCase(input=, actual_output=) split.",
        ),
        (
            "A smaller pre-built catalog than DeepEval",
            "~30 built-in metrics vs. DeepEval's ~50 - Opik covers the common RAG/agent "
            "cases well but has less long-tail coverage.",
        ),
        (
            "Same judge-model cost and nondeterminism as the others",
            "Every GEval.score() call is a real, billed request to the judge model, same "
            "tradeoffs as every other LLM-as-judge mechanism on this page.",
        ),
    ],
    "capability_map": [
        {"group": "Scoring", "capability": "GEval (custom criteria)",
         "description": "task_introduction + evaluation_criteria -> a 0-1 score and a reason",
         "status": "live"},
        {"group": "Scoring", "capability": "Built-in Metrics (~30)",
         "description": "Hallucination, Moderation, AnswerRelevance, ContextPrecision/Recall, and more",
         "status": "mentioned"},
        {"group": "Scoring", "capability": "BaseMetric (fully custom)",
         "description": "Subclass and implement your own scoring logic from scratch, beyond GEval's shape",
         "status": "mentioned"},
        {"group": "Scoring", "capability": "Guardrails",
         "description": "Validates output before it reaches the user, not just after the fact",
         "status": "mentioned"},

        {"group": "Tracing & ops", "capability": "Tracing (@opik.track)",
         "description": "Auto-instruments function calls into spans for later review",
         "status": "reference"},
        {"group": "Tracing & ops", "capability": "Experiments",
         "description": "Compares metric results across dataset and pipeline versions",
         "status": "reference"},
        {"group": "Tracing & ops", "capability": "Online Evaluation Rules",
         "description": "Runs metrics automatically against live production traces",
         "status": "reference"},
        {"group": "Tracing & ops", "capability": "Self-Hostable Backend",
         "description": "The full tracing/observability platform can run on your own infrastructure",
         "status": "mentioned"},

        {"group": "Extras", "capability": "Playground",
         "description": "Compares prompts and models side by side in a hosted UI",
         "status": "mentioned"},
        {"group": "Extras", "capability": "Dataset Management",
         "description": "Versioned datasets for repeatable experiment runs",
         "status": "mentioned"},
    ],
}

LANGSMITH_PROFILE = {
    "name": "LangSmith",
    "tagline": "LangChain's evaluation and observability platform - evaluators are just functions.",
    "links": {
        "site": "https://www.langchain.com/langsmith",
        "docs": "https://docs.smith.langchain.com/evaluation",
    },
    "how_it_works": (
        "A LangSmith evaluator is a plain Python function - `def evaluator(inputs, "
        "outputs, reference_outputs) -> dict`. `langsmith.evaluate()` runs one across a "
        "whole dataset and logs results to LangSmith's platform, but the function itself "
        "needs no LangSmith account at all to call directly, which is what this page's "
        "live demos do.\n\n"
        "`openevals` - a separate, lightweight library maintained by the LangChain team "
        "specifically to build these functions - is the closest LangSmith analog to "
        "G-Eval or AspectCritic: `create_llm_as_judge(prompt=..., continuous=True)` turns "
        "a `.format()`-style prompt template (`{inputs}`/`{outputs}`/`{reference_outputs}`) "
        "into a working evaluator function that returns a 0-1 score plus reasoning. Set "
        "`continuous=False` instead and the same function returns a boolean verdict - "
        "which is what this page's second demo uses to build a genuine A/B pairwise "
        "comparison, not just a pointwise score."
    ),
    "integration": (
        "`pip install openevals`, set `OPENAI_API_KEY`, and call the evaluator function "
        "directly - exactly this page's approach. Passing that same function to "
        "`langsmith.evaluate(target, data=dataset, evaluators=[evaluator])` is the fuller "
        "path: it runs your app against a whole logged dataset, applies every evaluator "
        "to every row, and pushes results into LangSmith's comparison UI - this needs "
        "`LANGSMITH_API_KEY`, which this page's demos deliberately don't require.\n\n"
        "LangSmith's own ecosystem leans on `evaluate_comparative()` for pairwise "
        "evaluation as a first-class runner, not a workaround - this page's pairwise "
        "demo builds the same idea manually with `create_llm_as_judge`, one level below "
        "that runner."
    ),
    "when_to_use": (
        "Reach for this stack when \"evaluator\" being a plain function is itself the "
        "value - no special base class, no required framework object, just something "
        "that takes inputs/outputs and returns a score. It's also the natural choice "
        "when a head-to-head comparison (\"is the new prompt better than the old one\") "
        "matters as much as an absolute score, since pairwise evaluation is a first-class "
        "concept here, not an afterthought.\n\n"
        "It's a weaker fit when you want a purpose-built object with a name and required "
        "fields (LLMTestCase, SingleTurnSample) that structurally enforces what a metric "
        "needs - `create_llm_as_judge`'s prompt is just a string template, so nothing "
        "stops you from writing a template that's missing what the judge actually needs "
        "to see."
    ),
    "impressive_points": [
        (
            "Pairwise comparison as a first-class concept",
            "evaluate_comparative() runs two versions of a pipeline against the same "
            "dataset and asks which is better - a genuinely different judging shape from "
            "every pointwise-scoring demo on this page, and the reason this page earns a "
            "second live demo.",
        ),
        (
            "An evaluator is just a function",
            "No required base class or object - def evaluator(inputs, outputs) -> dict is "
            "a complete, valid evaluator. Nothing to subclass, nothing to configure "
            "beyond what you'd write anyway.",
        ),
        (
            "A large library of pre-written judge prompts",
            "openevals.prompts ships ~30 ready-made templates (hallucination, "
            "conciseness, RAG groundedness, code correctness, PII leakage, and more) as "
            "plain strings you can read, copy, and modify rather than opaque built-ins.",
        ),
        (
            "Deep, native LangChain/LangGraph tracing",
            "Because it's the same company's stack, tracing an existing LangChain or "
            "LangGraph app needs close to zero extra instrumentation.",
        ),
    ],
    "pain_points": [
        (
            "choices is documented as floats, not labels",
            "create_llm_as_judge's `choices` parameter is typed as a list of floats for a "
            "discrete numeric scale - it's not the mechanism for a labeled A/B choice. "
            "We built the pairwise demo with continuous=False (a boolean question: \"is A "
            "better?\") instead, which is the well-supported path, rather than fighting "
            "choices into doing something it isn't documented for.",
        ),
        (
            "Two different templating conventions to keep straight",
            "openevals prompts use plain .format()-style {inputs}/{outputs} placeholders "
            "- easy to reach for autoevals' {{mustache}} syntax by habit if you're working "
            "across both libraries in the same session, as this page's build did.",
        ),
        (
            "No dedicated custom-metric object",
            "Same shape of gap as TruLens: there's no LLMTestCase- or SingleTurnSample- "
            "style object that enforces what fields a judge prompt needs - a template "
            "string with a typo in a placeholder name just silently renders wrong.",
        ),
        (
            "Same judge-model cost and nondeterminism as the others",
            "Every create_llm_as_judge call is a real, billed request to the judge model, "
            "same tradeoffs as every other LLM-as-judge mechanism on this page.",
        ),
    ],
    "capability_map": [
        {"group": "Scoring", "capability": "Custom Evaluator Functions",
         "description": "Any Python function returning a score - no required base class",
         "status": "foundational"},
        {"group": "Scoring", "capability": "create_llm_as_judge (pointwise)",
         "description": "A .format()-style prompt template becomes a working 0-1 or boolean judge",
         "status": "live"},
        {"group": "Scoring", "capability": "Pairwise / Comparative Evaluation",
         "description": "Judges two candidate outputs head to head instead of scoring one in isolation",
         "status": "live"},
        {"group": "Scoring", "capability": "Pre-Written Judge Prompt Library (~30)",
         "description": "Hallucination, conciseness, RAG groundedness, PII leakage, and more, as readable templates",
         "status": "mentioned"},

        {"group": "Tracing & ops", "capability": "Native LangChain/LangGraph Tracing",
         "description": "Near-zero-instrumentation tracing for apps already built on that stack",
         "status": "reference"},
        {"group": "Tracing & ops", "capability": "Online Evaluation / Monitoring",
         "description": "Runs evaluators automatically against live production traces",
         "status": "reference"},
        {"group": "Tracing & ops", "capability": "Annotation Queues",
         "description": "Routes traces to a person for manual review and labeling",
         "status": "mentioned"},

        {"group": "Extras", "capability": "Datasets & Experiments",
         "description": "Versioned datasets with side-by-side experiment comparison",
         "status": "mentioned"},
        {"group": "Extras", "capability": "Prompt Hub",
         "description": "Versioned, shareable prompt templates",
         "status": "mentioned"},
        {"group": "Extras", "capability": "Playground",
         "description": "Compares prompts and models side by side in a hosted UI",
         "status": "mentioned"},
    ],
}

PHOENIX_PROFILE = {
    "name": "Arize Phoenix",
    "tagline": "OpenTelemetry-native LLM observability, with categorical rather than continuous evals.",
    "links": {
        "site": "https://phoenix.arize.com",
        "docs": "https://arize.com/docs/phoenix",
    },
    "how_it_works": (
        "Phoenix's `phoenix.evals` builds an `LLM` wrapper around a provider, then "
        "`create_classifier(name, prompt_template, llm, choices)` builds an evaluator "
        "where `choices` is a dict mapping named labels to `(score, description)` pairs - "
        "e.g. `{\"relevant\": (1, \"...\"), \"irrelevant\": (0, \"...\")}`. Calling "
        "`.evaluate({...})` returns a list of `Score` objects, each with `.label`, "
        "`.score`, and `.explanation`.\n\n"
        "That's the one genuinely different shape on this whole page: every other "
        "framework's custom-criteria demo returns a continuous 0-1 number (or a bare "
        "binary flag). Phoenix's classifier is categorical by design - you get back a "
        "named label plus an explanation, matching how Phoenix's own pre-built "
        "evaluators work (hallucination detection returns \"hallucinated\"/\"factual\", "
        "not a score you have to interpret)."
    ),
    "integration": (
        "`pip install arize-phoenix-evals`, set `OPENAI_API_KEY`, build an `LLM(provider=`"
        "`\"openai\", model=...)`, and call `create_classifier(...).evaluate({...})` "
        "directly - no Phoenix server or account needed for scoring, exactly this page's "
        "approach.\n\n"
        "Phoenix's fuller integration path is OpenTelemetry-native tracing: instrument an "
        "app with the `openinference` auto-instrumentors, run a local (or hosted) Phoenix "
        "server, and `evaluate_dataframe`/`async_evaluate_dataframe` scores whole "
        "collections of spans pulled from those traces - closer to TruLens's or Opik's "
        "trace-first model than to DeepEval's inline-call model."
    ),
    "when_to_use": (
        "Reach for Phoenix's classifier when a label plus an explanation is a more "
        "honest fit for the judgment than a number - \"is this hallucinated\" is a "
        "yes/no/explain question, not really a 0.73. It's also a strong fit if OTel-"
        "native tracing across your whole stack (not just LLM calls) is already how your "
        "team does observability.\n\n"
        "It's a weaker fit when you specifically want a single continuous score to "
        "average across a dataset or chart over time - a categorical label needs an "
        "extra mapping step to turn into that kind of number, where G-Eval, AspectCritic, "
        "or Opik's GEval give you the float directly."
    ),
    "impressive_points": [
        (
            "Categorical, not continuous, by design",
            "create_classifier returns a named label plus an explanation, not a bare "
            "float - a genuinely different, arguably more honest shape for judgments "
            "like \"is this hallucinated\" than a 0-1 score everyone reads differently.",
        ),
        (
            "OpenTelemetry-native, industry-standard tracing",
            "Built on the openinference OTel semantic conventions, so traces are portable "
            "to any OTel backend, not locked to Phoenix's own viewer.",
        ),
        (
            "A long, well-labeled pre-built template library",
            "Ready-made classifiers for hallucination, toxicity, QA correctness, RAG "
            "relevance, and more, each with a documented choice/label scheme rather than "
            "an opaque score.",
        ),
        (
            "Started as an embeddings/drift tool, still shows",
            "Phoenix's roots are in visualizing embedding drift and cluster shifts in "
            "production data - a different lens on \"is something wrong\" than any other "
            "framework here offers, even though this page's live demo doesn't reach that "
            "far.",
        ),
    ],
    "pain_points": [
        (
            "A label needs an extra step to become a trend line",
            "If you want to chart \"average helpfulness over time\", a categorical label "
            "has to be mapped to a number first - Phoenix's choices dict does that "
            "mapping, but it's one more thing to define than a framework that just "
            "returns a float.",
        ),
        (
            "The API has moved under docs written for an older version",
            "phoenix.evals has been restructured recently (create_classifier is the "
            "current entry point); some tutorials and search results still describe an "
            "older llm_classify()-based API that no longer matches what pip installs "
            "today - worth checking the installed version's own API before copying an "
            "example.",
        ),
        (
            "Needs its own LLM wrapper object",
            "You construct an LLM(provider=, model=) once and pass it into every "
            "classifier - one more object in the chain than frameworks that just take a "
            "model name string directly.",
        ),
        (
            "Same judge-model cost and nondeterminism as the others",
            "Every classifier.evaluate() call is a real, billed request to the judge "
            "model, same tradeoffs as every other LLM-as-judge mechanism on this page.",
        ),
    ],
    "capability_map": [
        {"group": "Scoring", "capability": "Custom Classifiers (create_classifier)",
         "description": "Named labels, each mapped to a score and a description - not a bare float",
         "status": "live"},
        {"group": "Scoring", "capability": "Pre-Built Eval Templates",
         "description": "Hallucination, toxicity, QA correctness, RAG relevance, and more",
         "status": "mentioned"},
        {"group": "Scoring", "capability": "Structured Extraction Evals",
         "description": "Checks whether a model's structured/JSON output matches an expected schema",
         "status": "mentioned"},

        {"group": "Tracing & ops", "capability": "OpenTelemetry-Native Tracing",
         "description": "Built on openinference OTel conventions - portable to any OTel backend",
         "status": "mentioned"},
        {"group": "Tracing & ops", "capability": "evaluate_dataframe",
         "description": "Scores whole collections of spans pulled from traces, not just single calls",
         "status": "reference"},
        {"group": "Tracing & ops", "capability": "Embeddings & Drift Visualization",
         "description": "UMAP-based views of embedding drift and cluster shifts in production data",
         "status": "reference"},

        {"group": "Extras", "capability": "Dataset & Experiment Tracking",
         "description": "Versioned datasets with experiment comparison",
         "status": "mentioned"},
        {"group": "Extras", "capability": "Session/Ops Dashboard",
         "description": "A hosted or local UI for browsing traces and eval results",
         "status": "reference"},
    ],
}

LANGFUSE_PROFILE = {
    "name": "Langfuse",
    "tagline": "Open-source LLM observability with no built-in judge - you push scores in.",
    "links": {
        "site": "https://langfuse.com",
        "docs": "https://langfuse.com/docs",
    },
    "how_it_works": (
        "Langfuse's core model is traces (a session, or one request) made of "
        "observations (spans, generations). It captures those in detail - inputs, "
        "outputs, latency, cost, token counts - and lets you attach scores to them via "
        "`langfuse.create_score(trace_id=, name=, value=, comment=)`. What it doesn't do "
        "is compute those scores itself: there's no G-Eval, no AspectCritic, no GEval "
        "here. Langfuse is a sink you push evaluation results into, from whatever judge "
        "you already have - one of this project's own DeepEval/Ragas/TruLens scores, a "
        "hand-written rule, or (as this page's demo shows) a plain OpenAI call you write "
        "yourself.\n\n"
        "This is a deliberate design choice, not a missing feature - Langfuse's docs "
        "describe this as staying focused on observability and letting you bring "
        "whichever evaluation approach fits, rather than picking one judging mechanism "
        "for you."
    ),
    "integration": (
        "`pip install langfuse`, set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` (a "
        "real account or self-hosted instance - there's no scoring path that avoids this "
        "the way autoevals or Opik's GEval avoid needing their own platform key, because "
        "pushing a score IS the integration). `create_trace_id()` generates an ID "
        "locally with no network call; `create_score(...)` queues the score, and "
        "`flush()` is what actually sends it.\n\n"
        "One real gotcha this page's build hit: `create_score()` and `flush()` are "
        "fire-and-forget - they don't raise a catchable exception on bad credentials, "
        "they just log an error internally and return normally. `auth_check()` is the "
        "one call that does raise cleanly, so this page calls it up front before pushing "
        "anything, rather than trusting flush() to report failure."
    ),
    "when_to_use": (
        "Reach for Langfuse when tracing, cost tracking, and prompt versioning across "
        "your whole app matter more than which specific judging mechanism computes a "
        "score - and when you already have (or want to build) your own evaluation logic "
        "rather than adopting a framework's built-in judge.\n\n"
        "It's a weaker fit as a starting point if you have no scoring logic yet and want "
        "one framework to hand you both the judge and the place to see the results - "
        "every other framework on this page gives you a working judge in a few lines; "
        "Langfuse gives you the place to put the judge's output, and expects you to "
        "supply the judge."
    ),
    "impressive_points": [
        (
            "Honest about not being a judge",
            "\"No built-in judges - you push scores in\" isn't a gap Langfuse is hiding; "
            "it's a stated design choice that keeps it from being locked into one "
            "opinionated grading mechanism.",
        ),
        (
            "Fully open-source and self-hostable",
            "The whole platform, not just a client SDK, can run on infrastructure you "
            "control - a stronger self-hosting story than most of the platform-first "
            "tools on this page.",
        ),
        (
            "Deep cost and token accounting",
            "Traces capture token counts and cost per call automatically, giving a "
            "real-money view of an eval run alongside the scores themselves.",
        ),
        (
            "Scores compose from anywhere",
            "Because there's no built-in judge to be locked into, a score pushed in can "
            "come from this project's own DeepEval, Ragas, or TruLens adapters just as "
            "easily as from a hand-written rule - Langfuse doesn't care about the source.",
        ),
    ],
    "pain_points": [
        (
            "create_score() and flush() don't raise on failure",
            "A bad API key doesn't throw a catchable exception at the point you'd expect "
            "- it logs an error and returns normally, so a naive try/except around those "
            "two calls alone would silently report success. auth_check() is the call "
            "that actually raises cleanly, which is why this page checks it first.",
        ),
        (
            "There's genuinely no judge to demo",
            "Every other framework on this page has a \"define a metric, get a score\" "
            "moment. Langfuse doesn't, by design - this page's live demo has to write and "
            "show its own plain OpenAI scoring call just to have something to push, which "
            "is a real difference in kind, not just in code.",
        ),
        (
            "Its own platform account is unavoidable",
            "Unlike autoevals, Opik's GEval, or DeepEval's Synthesizer, there's no way to "
            "exercise the actual integration (pushing a score) without a real Langfuse "
            "account - the scoring half can be tested standalone, but the point of this "
            "framework is the push, and that needs credentials.",
        ),
        (
            "Two separate keys to keep straight",
            "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are both required and easy to "
            "transpose, since most other tools on this page need only one credential.",
        ),
    ],
    "capability_map": [
        {"group": "Scoring", "capability": "Score Push API (create_score)",
         "description": "Attaches a score - from any judge you supply - to a real trace",
         "status": "live"},
        {"group": "Scoring", "capability": "No Built-In Judge",
         "description": "Deliberately ships no G-Eval-style mechanism of its own - bring your own scoring logic",
         "status": "foundational"},

        {"group": "Tracing & ops", "capability": "Tracing & Observations",
         "description": "Captures sessions, spans, and generations with inputs, outputs, latency, and cost",
         "status": "mentioned"},
        {"group": "Tracing & ops", "capability": "Cost & Token Accounting",
         "description": "Per-call token counts and real cost tracked automatically",
         "status": "mentioned"},
        {"group": "Tracing & ops", "capability": "Human Annotation Queues",
         "description": "Routes traces to a person for manual scoring",
         "status": "mentioned"},

        {"group": "Extras", "capability": "Prompt Management",
         "description": "Versioned, hosted prompt templates fetched at runtime",
         "status": "mentioned"},
        {"group": "Extras", "capability": "Datasets & Experiments",
         "description": "Versioned test sets with experiment-run comparison",
         "status": "mentioned"},
        {"group": "Extras", "capability": "Self-Hostable",
         "description": "The full platform, not just a client SDK, can run on your own infrastructure",
         "status": "mentioned"},
    ],
}

GARAK_PROFILE = {
    "name": "Garak",
    "tagline": "NVIDIA's LLM vulnerability scanner - attacks a model, doesn't grade an answer.",
    "links": {
        "site": "https://github.com/NVIDIA/garak",
        "docs": "https://docs.garak.ai",
    },
    "how_it_works": (
        "Garak is fundamentally different from everything else on this page: it's a "
        "red-team scanner, not a scoring framework. A probe is a set of adversarial "
        "prompts built to elicit one specific bad behavior (jailbreaks, data leakage, "
        "toxic continuations, encoded-payload smuggling, and dozens of other "
        "categories); a detector checks each response for whether the attack actually "
        "worked. `garak --probes <name> --model_type openai --model_name <model>` sends "
        "every prompt in that probe to a real model and reports a pass rate.\n\n"
        "Garak ships hundreds of probes, and their size varies enormously - some are a "
        "single prompt, some are 150+. A real trap this page's build hit directly: many "
        "probe classes' `recommended_detector` attribute is deprecated and defaults to "
        "`always.Fail`, a testing placeholder that reports every single generation as a "
        "vulnerability regardless of what the model actually said. The real, current "
        "detector lives on `primary_detector` instead - checking the wrong attribute "
        "looks like every probe has no meaningful automated scoring at all, when most "
        "genuinely do."
    ),
    "integration": (
        "`pip install garak`, set `OPENAI_API_KEY` (garak's openai generator reads it "
        "directly), then run the CLI - there's a Python API too "
        "(`garak._plugins.load_plugin(...)`), but the CLI is the documented, "
        "supported entry point, and it's what this page's live demo shells out to, same "
        "pattern as the Promptfoo page.\n\n"
        "A real run writes a `.report.jsonl` with one line per event: `attempt` entries "
        "(prompt, model output, per-detector scores - written twice, once right after "
        "generation and again after detection fills in the scores) and a summary `eval` "
        "entry (pass/fail counts). This page parses that file directly rather than "
        "scraping the CLI's pretty-printed table output."
    ),
    "when_to_use": (
        "Reach for Garak specifically when the question is adversarial robustness - can "
        "this model be jailbroken, tricked into leaking data, or talked into generating "
        "malware - not answer quality. It's the right tool when \"does this pass a "
        "safety review\" is the actual ask, which none of the other nine frameworks on "
        "this page are built to answer.\n\n"
        "It's the wrong tool for grading a specific answer's helpfulness, faithfulness, "
        "or correctness - Garak has no concept of \"the right answer\" to compare "
        "against; it only has \"did the attack work\". Use one of the other nine "
        "frameworks for that, and Garak specifically for red-teaming."
    ),
    "impressive_points": [
        (
            "A genuinely different question than every other framework here",
            "Nine frameworks on this page ask \"is this answer good\"; Garak asks \"can "
            "this model be broken\" - a different axis of evaluation entirely, and the "
            "reason it earns a spot on this page despite fitting none of the other "
            "demos' shapes.",
        ),
        (
            "Hundreds of probes across a real taxonomy",
            "Jailbreaks, prompt injection, data leakage, malware generation, encoding "
            "smuggling, bias, and more - each probe's tags map to OWASP LLM Top 10 and "
            "AVID taxonomy codes, not an ad-hoc category list.",
        ),
        (
            "Works against any generator, not just OpenAI",
            "The same probe runs unchanged against a local Hugging Face model, a "
            "different API provider, or a custom generator class - the attack is "
            "decoupled from the target.",
        ),
        (
            "A real, structured report, not just a terminal table",
            "The JSONL report captures every prompt, every raw output, and every "
            "detector score - enough to build exactly the kind of custom view this "
            "page's live demo does, rather than only a pass/fail percentage.",
        ),
    ],
    "pain_points": [
        (
            "recommended_detector is a deprecated trap",
            "We hit this directly: checking a probe's `.recommended_detector` attribute "
            "shows `['always.Fail']` for nearly every probe, which looks like none of "
            "them have real scoring. The actual, current detector is on "
            "`.primary_detector` - a single string, not a list - and `recommended_"
            "detector` only still exists for backward compatibility.",
        ),
        (
            "always.Fail is a real, live placeholder detector",
            "It's not a bug or a misconfiguration - `always.Fail` literally always "
            "returns 1.0 (\"vulnerable\") no matter what the model said, meant for "
            "testing garak itself. A probe genuinely paired with it by default has no "
            "real automated scoring; you'd need to specify your own detector or read the "
            "raw output yourself.",
        ),
        (
            "Probe sizes vary from 1 prompt to 150+",
            "Picking a probe for a fast live demo means checking `len(probe.prompts)` "
            "directly - the CLI and docs don't surface size prominently, and a wrong "
            "pick turns a 10-second demo into a 10-minute one.",
        ),
        (
            "A run can retry for a long time before failing",
            "Same shape of issue as Promptfoo: on a genuine provider failure, garak's "
            "generator retries with backoff before giving up, so a broken run can take "
            "minutes to report an error rather than seconds.",
        ),
    ],
    "capability_map": [
        {"group": "Scanning", "capability": "Probe Library (hundreds)",
         "description": "Jailbreaks, injection, data leakage, malware generation, encoding smuggling, and more",
         "status": "live"},
        {"group": "Scanning", "capability": "Detector Library",
         "description": "Pattern-based and semantic checks for whether an attack actually succeeded",
         "status": "foundational"},
        {"group": "Scanning", "capability": "Generator Plugins",
         "description": "Runs the same probe against any model - API providers, local HF models, custom classes",
         "status": "mentioned"},
        {"group": "Scanning", "capability": "Buff/Harness Pipeline",
         "description": "Pluggable pre/post-processing stages around a scan (paraphrasing, translation, etc.)",
         "status": "mentioned"},

        {"group": "Workflow & ops", "capability": "Structured JSONL Reports",
         "description": "Every prompt, raw output, and detector score, not just a pass/fail summary",
         "status": "mentioned"},
        {"group": "Workflow & ops", "capability": "HTML Digest",
         "description": "A browsable summary report generated alongside the raw JSONL",
         "status": "mentioned"},
        {"group": "Workflow & ops", "capability": "OWASP/AVID Taxonomy Mapping",
         "description": "Every probe's findings tag to a recognized vulnerability taxonomy code",
         "status": "mentioned"},
        {"group": "Workflow & ops", "capability": "CI-Friendly Scanning",
         "description": "Runs headless from the CLI with a real exit code, suitable for a build pipeline",
         "status": "mentioned"},
    ],
}
