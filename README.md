# LLM Evaluation Ecosystem — 11 Frameworks, Live

A hands-on tour of the LLM evaluation and safety-testing landscape: eleven separate frameworks — DeepEval, Ragas, TruLens, Opik, Braintrust, Arize Phoenix, LangSmith, Langfuse, Promptfoo, Garak, and Guardrails AI — each one given its own page in a single Streamlit app, with a real API call or a real CLI process behind every number on screen. Nothing here is a screenshot, a mock, or canned output.

## 🎥 Demo Video

An ~8-minute walkthrough: the pattern this project follows, then a deep dive on the most interesting real bugs and design decisions this build actually surfaced.

**▶ [Watch on YouTube](PASTE_YOUTUBE_LINK_HERE)**

*(Replace the link above with your video's URL once the upload finishes — it's the only edit this README needs before it's complete.)*

---

## Why this exists

There are more than a dozen LLM evaluation frameworks in active use right now, and most of them market themselves as solving the same problem. Reading the docs tells you what a framework *claims* — it doesn't tell you what breaks the moment you actually wire it up: hidden defaults, version conflicts with the rest of your stack, deprecated attributes still shipped as if they were current, background network calls you never asked for.

So every framework's page in this app follows the same two-part structure:

1. **A full capability map** — an honest, text-only inventory of everything that framework's own documentation claims, labeled as either **proven live** (run for real, right here), **foundational** (the underlying mechanism is shown in code even if not clicked live), or **just worth knowing exists** (documented, not demoed).
2. **One or two live demos** — a real network call to OpenAI, or a real CLI subprocess, running while you watch, wired to that framework's actual, distinctive mechanism rather than a generic wrapper.

The point isn't full coverage of every feature. It's proof that the integration actually works.

## The 11 frameworks

| Framework | What makes it different | Live demo(s) |
|---|---|---|
| **DeepEval** | Open-source, built to feel like pytest for LLM outputs | G-Eval (criteria → judge metric); Synthesizer (invents test cases from scratch) |
| **Ragas** | RAG evaluation organized around one taxonomy: Retrieval / Generation / End-to-end | AspectCritic (binary criteria check); all three taxonomy metrics at once |
| **TruLens** | Coined the "RAG Triad"; feedback functions over traces | Custom criteria via `generate_score_and_reasons`; the RAG Triad live (3 checks, 1 call) |
| **Opik** | Comet's open-source eval + observability library | `GEval` — the same plain-English-criteria idea, Comet's implementation |
| **Braintrust** | `autoevals` — a standalone scoring library, decoupled from the hosted platform | `LLMClassifier` — write the full grading prompt and choice-to-score map yourself |
| **Arize Phoenix** | OpenTelemetry-native; categorical labels, not floats | `create_classifier` — a real label out, not a continuous score |
| **LangSmith** | LangChain's eval platform; evaluators are just functions | `create_llm_as_judge`; a genuine pairwise "which answer is better" comparison |
| **Langfuse** | No built-in judge at all — you push scores in | A real OpenAI scoring call, then a real trace pushed to a live Langfuse dashboard |
| **Promptfoo** | A YAML-configured CLI, not a Python library | Generate-then-grade in one `promptfoo eval` run; `promptfoo redteam run` attacking the actual prompt template |
| **Garak** | NVIDIA's model-level vulnerability scanner — attacks the model, not the answer | `goodside.WhoIsRiley` probe, live against a real model |
| **Guardrails AI** | Validates and enforces *structure* — never scores free text with a judge | A custom `Validator`; `Guard.for_pydantic` — the LLM call itself, schema-enforced |

## Quickstart

```bash
git clone <this-repo-url>
cd llm-frameworks
uv sync
cp .env.example .env   # then fill in at least OPENAI_API_KEY
uv run streamlit run framework/app.py
```

Every page needs only `OPENAI_API_KEY`, except Langfuse's live demo (also needs `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`) and Promptfoo/Garak, which additionally need their own CLI installed:

```bash
npm install -g promptfoo   # Node.js required
uv tool install garak      # or: pipx install garak
```

(Garak and Promptfoo are kept out of `pyproject.toml` on purpose — see [PROBLEMS.md](PROBLEMS.md) for why.)

## Project layout

```
framework/
  app.py            — the Streamlit page itself (sidebar nav + all 11 framework views)
  catalog.py         — capability maps, pain points, impressive points (frameworks 1-4)
  catalog2.py         — same, for frameworks 5-11
  live_*.py           — one real adapter per framework: a run_*() function that makes
                          the actual call, and a build_code_snippet() showing exactly
                          what ran
  samples.py           — shared example inputs/outputs the demos use
schema/
  env_config.py         — the one shared helper (check_openai, check_langfuse, etc.)
```

---

## Problems I faced while integrating these frameworks

Every framework here has real, undocumented gotchas that only surface once you actually wire up a live integration — hidden gateway defaults, version conflicts, deprecated attributes still shipped as current, background network calls nobody asked for.

**→ Full write-up: [PROBLEMS.md](PROBLEMS.md)**
