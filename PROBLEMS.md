# Problems I faced while integrating these frameworks

This is the part the vendor docs don't cover. Every item below is something I hit directly while wiring up a real, working integration for the [llm-frameworks](README.md) project — not a hypothetical or a docs quote.

## Dependency conflicts across the ecosystem

The single biggest recurring issue building this project wasn't any one framework's API — it was getting *all eleven* to install into the same Python environment at once.

- **Garak vs. Ragas/TruLens.** Garak's current release needs `langchain>=1.3.14` and `openai>=2.0`. Ragas 0.3.1 hard-imports `langchain_community.chat_models.vertexai`, which only exists on the older `langchain-community` 0.3.x line, and `trulens-providers-openai` needs `openai<2.0`. Those three requirements are mutually exclusive in one dependency tree — a genuine, current ecosystem conflict, not a pinning mistake on my part. **Fix:** Garak is installed standalone (`uv tool install garak`, isolated from this project's own venv) and invoked purely as a CLI binary over `PATH` — `live_garak.py` never imports it as a library, it shells out with `subprocess`.
- **Guardrails AI hit the exact same fault line.** `guardrails-ai==0.11.0` requires `openai>=2.0`, which conflicts with `trulens-providers-openai`'s `openai<2.0` pin already in this project. Rather than pushing Guardrails out to its own standalone install too, I found that the `0.10.x` line only requires `openai<3.0` (not `>=2.0`) — and confirmed directly that the exact API surface this project uses (`Guard.for_pydantic`, the custom-validator base class) is unchanged between `0.10.2` and `0.11.0`. **Fix:** pinned to `guardrails-ai>=0.10.0,<0.11.0` instead of latest.
- **Promptfoo needed the same standalone treatment as Garak**, for a simpler reason: it's a Node.js CLI, not a Python package at all. `npm install -g promptfoo` and invoke over `PATH`, same pattern as Garak.

## DeepEval
- Every `metric.measure()` call is a real, billed request to the judge model — there's no free local mode, and cost/latency scale directly with dataset size.
- Scoring is nondeterministic by default; `strict_mode` fixes that but collapses the nuanced 0–1 score down to a blunt pass/fail.
- **Hit for real:** a judge call in this project's own RAG station threw `RetryError[TimeoutError]` on a slow/rate-limited response and took the whole metric down with it — the reason every adapter here is wrapped in its own try/except, so one framework's flaky call never sinks an entire run's other results.
- The Synthesizer produces plausible-looking test cases fast, but "plausible" isn't "correct" — a generated `expected_output` needs a human check before it's trusted as ground truth.

## Ragas
- `AspectCritic.single_turn_score()` returns a bare 0/1 float — no free-text reasoning ships with it (confirmed straight from its own source, whose return type is just `float`), which is why this page's Ragas demo has no "why" panel for that metric.
- **A real bug I hit:** `AnswerCorrectness(llm=, embeddings=)` constructs without error, but the moment you call it, it raises `AssertionError: AnswerSimilarity must be set`. It silently needs a `SemanticSimilarity` instance built first and passed in as `answer_similarity=` — undocumented in the constructor signature itself.
- Just importing `ragas.testset.TestsetGenerator` pulls in a `tiktoken` download and a full knowledge-graph pipeline (embeddings, theme extraction, scenario generation) — far too heavy for a fast live demo, which is why the Ragas page's second demo stays with the metric taxonomy instead.
- Nothing in a Ragas metric's name tells you which taxonomy bucket (Retrieval/Generation/End-to-end) it belongs to — you either read the docs or the source's `required_columns`.

## TruLens
- No `CustomMetric(criteria=...)` object exists — defining your own criteria means building the system/user prompt yourself from TruLens's own template strings.
- `generate_score_and_reasons` judges one blob of text (`SUBMISSION`), with no separate question/answer split the way DeepEval's `LLMTestCase` has — the question has to be folded into the submission text itself.
- **A labeling mistake I actually shipped at one point:** `context_relevancy` mislabeled as `context_precision` — two genuinely different concepts (an LLM judging one document's relevance, vs. real set-overlap math against a labeled relevant-docs set) that TruLens's own naming does little to prevent confusing.
- `groundedness_measure_with_cot_reasons` silently pulls in NLTK's `punkt_tab` sentence tokenizer, downloading its data file over the network the first time it runs — a hidden dependency beyond the OpenAI call itself.
- `generate_score_and_reasons` tries structured JSON first, falls back to parsing a text block, and if that still fails, fires a *second* LLM call just to reformat the first response — resilient, but means one feedback call can silently become two billed calls.

## Opik
- `GEval(track=True)` is the constructor default — leave it unset and every score call tries to log to Opik's backend, which needs credentials this project deliberately avoids requiring.
- `score(output=...)` has no separate input field; the question/context has to be folded into `task_introduction` as a string.
- A smaller pre-built metric catalog than DeepEval (~30 vs. ~50) — solid on common RAG/agent cases, less long-tail coverage.

## Braintrust
- **The headline bug of this whole project:** a real `401 Unauthorized` error, on a completely valid OpenAI key. Braintrust's scoring library, `autoevals`, silently defaults to routing every request through Braintrust's *own* AI gateway (`gateway.braintrust.dev`) rather than straight to OpenAI, unless you explicitly hand it a real client object. A plain, working API key gets sent to the wrong service and rejected — and the error message gives no hint why. **Fix:** construct `client=OpenAI()` yourself and pass it into `LLMClassifier(..., client=OpenAI())`, which bypasses the gateway-routing logic entirely. One line, but only findable by reading the library's actual source.
- "Braintrust" the hosted platform and `autoevals` the scoring library are separate installs with separate docs — easy to conflate, since most tutorials assume you want both.
- `autoevals`'s `prompt_template` uses `{{mustache}}` syntax, while `openevals` (LangSmith's library) uses plain `{python}`.format()-style placeholders — an easy mix-up working across both in the same session.

## Arize Phoenix
- A categorical label needs an explicit `choices` dict to become a numeric trend line — one more thing to define than a framework that just returns a float.
- The API has moved out from under some of its own tutorials: `create_classifier` is the current entry point, but search results and some docs still describe an older `llm_classify()`-based API that no longer matches what `pip install` gives you today.
- Needs its own `LLM(provider=, model=)` wrapper object constructed once and passed into every classifier, rather than a plain model-name string.

## LangSmith
- `create_llm_as_judge`'s `choices` parameter is documented as a list of **floats** for a discrete numeric scale — not the mechanism for a labeled A/B choice, despite how it reads at first glance. Built the pairwise demo with `continuous=False` (a boolean "is A better?" question) instead of fighting `choices` into a role it isn't documented for.
- Two templating conventions to keep straight in the same session: `openevals` uses plain `{python}`.format() placeholders, `autoevals` uses `{{mustache}}` — easy to reach for the wrong one out of habit.
- No dedicated custom-metric object, same gap as TruLens — a typo in a template placeholder name just silently renders wrong, with nothing enforcing the required fields.

## Langfuse
- **A real trap:** `create_score()` and `flush()` don't raise on a bad API key — they log an error internally and return normally. A naive `try/except` around just those two calls would silently report success on a failed push. `auth_check()` is the call that actually raises cleanly, so this project checks that first.
- There's genuinely no judge here, by design — every other framework has a "define a metric, get a score" moment; Langfuse's own demo has to write and show a plain OpenAI scoring call just to have something to push.
- The actual integration (pushing a score) can't be exercised at all without a real Langfuse account and both `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` — two credentials to keep straight, versus one for most of the other frameworks here.

## Promptfoo
- It's a CLI, not a library — there's no in-process Python or JS API. Integrating it means shelling out with `subprocess` and parsing the JSON it writes back, exactly what `live_promptfoo.py` does.
- `promptfoo eval` phones home to telemetry and update-check endpoints by default — `PROMPTFOO_DISABLE_TELEMETRY` and `PROMPTFOO_DISABLE_UPDATE_CHECK` are both needed to run cleanly in a sandboxed environment.
- On a genuine provider failure, the retry backoff can make a working integration look hung: a single `eval` run can take well over a minute to fail cleanly. `redteam run` is worse — confirmed directly, its local generation step retried against a blocked connection for **over 170 seconds** without giving up, versus a few dozen seconds for plain `eval`.
- **`redteam run` has its own hidden account/cloud layer, confirmed directly by running it:** it first tries an interactive `? Work email:` prompt on stdin, which hangs *forever* in a non-interactive process (like a server) unless `CI=true` is set. Separately, it calls Promptfoo's own cloud API to auto-infer your app's "purpose" unless `PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION=true` is explicitly set. Both had to be found and switched off to keep the red-team demo running on nothing but my own `OPENAI_API_KEY`.

## Garak
- **A real, easy-to-miss trap:** a probe's `.recommended_detector` attribute shows `['always.Fail']` for nearly every probe — looking like none of them have real automated scoring. The actual, current detector lives on `.primary_detector` (a single string, not a list); `recommended_detector` only still exists for backward compatibility. `always.Fail` isn't a bug — it's a real, live placeholder that always reports "vulnerable" regardless of the model's actual output, meant for testing Garak itself.
- Probe sizes vary from a single prompt to 150+, and neither the CLI nor the docs surface size prominently — picking one for a fast demo means checking `len(probe.prompts)` directly, or a 10-second demo turns into a 10-minute one.
- Same retry-backoff issue as Promptfoo: a genuine provider failure can take minutes to report, not seconds.

## Guardrails AI
- **`Guard()` builds a telemetry client unconditionally, on by default.** It always constructs a `HubTelemetry` singleton pointed at a hardcoded Guardrails-owned endpoint, and `enable_metrics` defaults to `True` even with no config file present. Setting `settings.rc.enable_metrics = False` in-process stops new spans from being *recorded*, but confirmed directly: the exporter still gets *built* regardless, so a background flush attempt still fires once at interpreter shutdown.
- **Simply `import guardrails` tries to reach GitHub** — it checks for NLTK's `punkt` tokenizer data and, if it isn't cached locally, attempts to download it from a `raw.githubusercontent.com` URL. A hidden network dependency at import time, unrelated to which validator you actually use.
- `ValidationOutcome.validation_summaries` is only ever populated on a **fail** — confirmed directly, it's an empty list on a pass. Reading back *why* something passed means capturing that yourself, inside your own `validate()` method.
- The `openai>=2.0` version conflict described above under "Dependency conflicts."

---

## What running this project taught me

Every one of the findings above came from actually running the integration with a real key and a real (or deliberately blocked) network connection — not from reading documentation. Several of them (the Braintrust gateway default, the Garak detector trap, Guardrails' import-time network call, Promptfoo's interactive email prompt) are the kind of thing that only surfaces once you try to run a framework unattended, outside a human sitting at a terminal watching it — which is exactly the condition a production integration has to survive.
