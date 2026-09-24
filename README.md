# LLM Frameworks - live capability showcase

A standalone Streamlit page, one framework at a time: a full capability map
(honest text inventory of everything the framework does) plus one or two
narrow live demos that prove real API/CLI calls, not canned output.

Covers 11 frameworks: DeepEval, Ragas, TruLens, Opik, Braintrust, Phoenix,
LangSmith, Langfuse, Promptfoo, Garak, Guardrails AI.

Split out of the `eval_LLM` project into its own venv because Garak's
current release needs `langchain>=1.3.14` and `openai>=2.0`, both
incompatible with Ragas (needs the older `langchain-community` 0.3.x line)
and TruLens's OpenAI provider (needs `openai<2.0`) - a real, current
ecosystem conflict, not a pinning mistake.

## Setup

```bash
uv sync
cp .env.example .env   # already done if .env carried over from eval_LLM - fill in OPENAI_API_KEY at minimum
uv run streamlit run framework/app.py
```

Every page needs only `OPENAI_API_KEY` except Langfuse's (also needs
`LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`) and Guardrails AI's custom
validator demo (same `OPENAI_API_KEY` as everything else - no separate
account, confirmed by reading `guardrails.Guard`'s source directly).

### Promptfoo and Garak - installed standalone, not via `uv sync`

Both are CLIs this app shells out to (`subprocess`), never Python libraries
imported directly, so they're deliberately NOT in `pyproject.toml`:

```bash
npm install -g promptfoo          # Node.js required
uv tool install garak             # or: pipx install garak
```

Garak especially needs to stay out of this project's own venv - its
dependency tree (a newer langchain, a newer openai SDK, torch,
transformers, ...) directly conflicts with Ragas/TruLens's requirements.
Installing it with `uv tool install` / `pipx` keeps it fully isolated while
still putting a `garak` binary on PATH, which is all `framework/live_garak.py`
needs (it never imports garak as a library).

Garak's install can hit a build error in a transitive dependency (`ecoji`)
on some Python versions - if so, run `pip install "setuptools<81"` first
(in whatever environment you're installing garak's tool chain into) and
retry.

Promptfoo's red-team demo (`framework/live_promptfoo.py`'s `run_redteam`)
needs no separate Promptfoo Cloud account - it sets `CI=true` (skips an
interactive "Work email" prompt that would otherwise hang forever on
stdin) and `PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION=true` (keeps
generation on your own `OPENAI_API_KEY` instead of Promptfoo's cloud
API) itself - nothing extra to configure.

### Guardrails AI - pinned to the 0.10.x line, not the latest 0.11.x

`guardrails-ai==0.11.0` requires `openai>=2.0`, which conflicts with
`trulens-providers-openai`'s `openai<2.0` pin in this same project - the
same openai-major-version fault line that pushed Garak out to a standalone
install above. The 0.10.x line still allows `openai<3.0` without forcing
`>=2.0`, so it resolves cleanly:

```toml
"guardrails-ai>=0.10.0,<0.11.0",
```

Confirmed directly: `Guard.for_pydantic` and the custom-validator API this
project uses are unchanged between 0.10.2 and 0.11.0.

## Layout

- `framework/app.py` - the Streamlit page itself
- `framework/catalog.py` + `catalog2.py` - all the written content (capability
  maps, pain points, impressive points) per framework
- `framework/live_*.py` - one real adapter per framework, each with its own
  `run_*()` function that makes the actual call and a `build_code_snippet()`
  that shows exactly what ran
- `framework/samples.py` - the shared example inputs/outputs the demos use
- `schema/env_config.py` - the one shared helper (`check_openai`, etc.) this
  app depends on from its former home in `eval_LLM`
