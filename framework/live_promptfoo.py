"""
Real, live Promptfoo calls behind framework/app.py's Promptfoo page.

This page's demo looks different on purpose too, but for the opposite
reason from Langfuse: Promptfoo isn't a Python library at all - it's a
YAML-configured CLI (`promptfoo eval`). Both demos below write a tiny
config to a temp file and shell out to the real `promptfoo` binary,
exactly as you would from a terminal - genuinely live runs, just via a
subprocess instead of a Python import.

  #1 `run_eval` -> `promptfoo eval`. The one demo on this whole page where
     nothing is pre-written: every other framework here grades an answer
     you already typed. Promptfoo actually calls the provider to GENERATE
     the answer from your prompt template, then grades it with its own
     `llm-rubric` assertion type (a plain-English criteria, Promptfoo's
     own G-Eval analog) - prompt, live generation, and grading in one
     command.

  #2 `run_redteam` -> `promptfoo redteam run`. A genuinely different angle
     from Garak (this project's other red-teaming demo): Garak is a
     model-level academic security scanner running probes like
     goodside.WhoIsRiley against the raw model. This is app-specific,
     OWASP-mapped adversarial testing of the actual prompt template you'd
     ship - here, whether a customer-support agent can be talked into an
     unauthorized contractual promise (the `contracts` plugin), verified
     live against a real target.

Needs `promptfoo` on PATH (npm install -g promptfoo) and OPENAI_API_KEY.
`run_redteam` needs no separate Promptfoo Cloud account - see the env
overrides below for exactly why, verified by direct testing.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from schema.env_config import check_openai  # noqa: E402

JUDGE_MODEL_DEFAULT = "gpt-4o-mini"


def check_promptfoo_cli() -> bool:
    return shutil.which("promptfoo") is not None


@dataclass
class LivePromptfooResult:
    ok: bool
    generated_output: Optional[str] = None
    passed: Optional[bool] = None
    score: Optional[float] = None
    reason: Optional[str] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def _build_config(prompt_template: str, variable_value: str, criteria: str, model: str) -> str:
    return (
        "prompts:\n"
        f"  - {json.dumps(prompt_template)}\n"
        "providers:\n"
        f"  - id: openai:{model}\n"
        "tests:\n"
        "  - vars:\n"
        f"      message: {json.dumps(variable_value)}\n"
        "    assert:\n"
        "      - type: llm-rubric\n"
        f"        value: {json.dumps(criteria)}\n"
    )


def build_code_snippet(prompt_template: str, variable_value: str, criteria: str, model: str) -> str:
    config = _build_config(prompt_template, variable_value, criteria, model)
    return (
        "# promptfooconfig.yaml\n"
        f"{config}\n"
        "# then, on the command line:\n"
        "promptfoo eval -c promptfooconfig.yaml -o results.json --no-cache\n"
        "# the provider generates the response AND grades it against the rubric in one run"
    )


def run_eval(
    prompt_template: str,
    variable_value: str,
    criteria: str,
    model: str = JUDGE_MODEL_DEFAULT,
) -> LivePromptfooResult:
    snippet = build_code_snippet(prompt_template, variable_value, criteria, model)

    status = check_openai()
    if not status.present:
        return LivePromptfooResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make a real "
                "provider call. Add one to .env and rerun."
            ),
            code_snippet=snippet,
        )

    if not check_promptfoo_cli():
        return LivePromptfooResult(
            ok=False,
            error=(
                "The `promptfoo` CLI isn't on PATH in this environment. Install it with "
                "`npm install -g promptfoo` (Node.js required) and rerun."
            ),
            code_snippet=snippet,
        )

    try:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "promptfooconfig.yaml"
            output_path = Path(tmp) / "results.json"
            config_path.write_text(_build_config(prompt_template, variable_value, criteria, model))

            env = dict(os.environ)
            env["PROMPTFOO_DISABLE_TELEMETRY"] = "1"
            env["PROMPTFOO_DISABLE_UPDATE_CHECK"] = "1"

            start = time.monotonic()
            proc = subprocess.run(
                ["promptfoo", "eval", "-c", str(config_path), "-o", str(output_path),
                 "--no-cache", "-j", "1"],
                cwd=tmp, env=env, capture_output=True, text=True, timeout=180,
            )
            elapsed = time.monotonic() - start

            if not output_path.exists():
                return LivePromptfooResult(
                    ok=False,
                    error=f"promptfoo produced no results file. stderr: {proc.stderr[-500:]}",
                    latency_seconds=round(elapsed, 2),
                    code_snippet=snippet,
                )

            data = json.loads(output_path.read_text())
            rows = data.get("results", {}).get("results", [])
            if not rows:
                return LivePromptfooResult(
                    ok=False, error="promptfoo returned no rows.",
                    latency_seconds=round(elapsed, 2), code_snippet=snippet,
                )

            row = rows[0]
            if row.get("error"):
                return LivePromptfooResult(
                    ok=False, error=row["error"], latency_seconds=round(elapsed, 2),
                    code_snippet=snippet,
                )

            grading = row.get("gradingResult") or {}
            generated = (row.get("response") or {}).get("output") if isinstance(row.get("response"), dict) else None

            return LivePromptfooResult(
                ok=True,
                generated_output=generated,
                passed=bool(row.get("success")),
                score=float(row.get("score", 0.0)),
                reason=grading.get("reason"),
                latency_seconds=round(elapsed, 2),
                code_snippet=snippet,
            )
    except subprocess.TimeoutExpired:
        return LivePromptfooResult(
            ok=False,
            error="promptfoo didn't finish within 180s - likely a provider retry loop; try again.",
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LivePromptfooResult(ok=False, error=str(exc), code_snippet=snippet)


# ---------------------------------------------------------------------------
# Demo #2: promptfoo redteam run
#
# Chosen plugin: `contracts` ("tests for unauthorized contractual commitments
# and legal exposure") - safe content-wise (touches nothing harmful) and
# thematically exact for this project's running customer-support-agent
# example: can the agent be talked into promising a refund/guarantee the
# real policy doesn't cover? Strategy is `basic` only (no jailbreak
# strategies), keeping this small, fast, and non-adversarial in tone.
# ---------------------------------------------------------------------------
REDTEAM_PLUGIN = "contracts"

# Verified directly, by running this exact command with a fake key and
# reading the raw output - not assumed from docs:
REDTEAM_ENV_OVERRIDES = {
    "PROMPTFOO_DISABLE_TELEMETRY": "1",
    "PROMPTFOO_DISABLE_UPDATE_CHECK": "1",
    # Without this, `redteam run` first calls Promptfoo's OWN cloud API to
    # auto-infer the app's "purpose" and extract entities before it ever
    # reaches your configured provider - a second network dependency beyond
    # OPENAI_API_KEY. Verified directly: with this unset, a blocked-network
    # run spent its first ~90s retrying api.promptfoo.app/health and a
    # remote "purpose" extraction call (4 retries with backoff each) before
    # generation even started. With it set, that whole layer is skipped and
    # only OPENAI_API_KEY is ever needed - matching every other demo here.
    "PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION": "true",
    # redteam commands ask for a "Work email" the first time they run - an
    # interactive `? Work email:` prompt on stdin. Verified directly: run
    # from a subprocess with no TTY and no CI marker, it hangs forever
    # waiting for input that will never come, which would silently freeze
    # this Streamlit server on first click. CI mode (the same convention
    # Jest/ESLint/etc use - true when $CI is set) skips the prompt entirely
    # and uses a placeholder email instead.
    "CI": "true",
}


@dataclass
class RedteamProbe:
    prompt: str
    response: str
    held: bool
    reason: Optional[str] = None


@dataclass
class LiveRedteamResult:
    ok: bool
    total: Optional[int] = None
    held: Optional[int] = None
    probes: List[RedteamProbe] = field(default_factory=list)
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def _build_redteam_config(prompt_template: str, purpose: str, num_tests: int, model: str) -> str:
    return (
        "prompts:\n"
        f"  - {json.dumps(prompt_template)}\n"
        "providers:\n"
        f"  - id: openai:{model}\n"
        "redteam:\n"
        f"  purpose: {json.dumps(purpose)}\n"
        "  injectVar: message\n"
        "  plugins:\n"
        f"    - {REDTEAM_PLUGIN}\n"
        f"  numTests: {num_tests}\n"
        "  strategies:\n"
        "    - basic\n"
    )


def build_redteam_code_snippet(prompt_template: str, purpose: str, num_tests: int, model: str) -> str:
    config = _build_redteam_config(prompt_template, purpose, num_tests, model)
    return (
        "# promptfooconfig.yaml\n"
        f"{config}\n"
        "# then, on the command line (no Promptfoo Cloud account needed - see\n"
        "# REDTEAM_ENV_OVERRIDES for exactly why):\n"
        "promptfoo redteam run -c promptfooconfig.yaml -o results.json --no-cache\n"
        f"# 1. generates {num_tests} adversarial 'contracts' probes locally, using your own\n"
        "#    OPENAI_API_KEY as the generator - no Promptfoo Cloud call involved\n"
        "# 2. runs each probe against your actual prompt template and grades whether the\n"
        "#    target held the line, using the contracts plugin's own grader"
    )


def check_promptfoo_redteam_cli() -> bool:
    return check_promptfoo_cli()


def run_redteam(
    prompt_template: str,
    purpose: str,
    model: str = JUDGE_MODEL_DEFAULT,
    num_tests: int = 2,
) -> LiveRedteamResult:
    """Runs `promptfoo redteam run`: generate {num_tests} adversarial `contracts`
    probes against `prompt_template`, then evaluate the target's real
    responses against them - two real steps, one real command.

    Note on timing (verified directly): local test-case generation retries
    much more aggressively than plain `promptfoo eval` on a persistent
    connection failure - a blocked-network run was still retrying against
    api.openai.com past 170 seconds without giving up. A working key over a
    working network should finish in well under a minute for 2 tests of one
    plugin; the timeout below exists to bound the worst case, not the
    common one.
    """
    snippet = build_redteam_code_snippet(prompt_template, purpose, num_tests, model)

    status = check_openai()
    if not status.present:
        return LiveRedteamResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make a real "
                "generation or target call. Add one to .env and rerun."
            ),
            code_snippet=snippet,
        )

    if not check_promptfoo_cli():
        return LiveRedteamResult(
            ok=False,
            error=(
                "The `promptfoo` CLI isn't on PATH in this environment. Install it with "
                "`npm install -g promptfoo` (Node.js required) and rerun."
            ),
            code_snippet=snippet,
        )

    try:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "promptfooconfig.yaml"
            output_path = Path(tmp) / "results.json"
            config_path.write_text(_build_redteam_config(prompt_template, purpose, num_tests, model))

            env = dict(os.environ)
            env.update(REDTEAM_ENV_OVERRIDES)

            start = time.monotonic()
            proc = subprocess.run(
                ["promptfoo", "redteam", "run", "-c", str(config_path), "-o", str(output_path),
                 "--no-cache", "-j", "1"],
                cwd=tmp, env=env, capture_output=True, text=True, timeout=240,
            )
            elapsed = time.monotonic() - start

            if not output_path.exists():
                tail = (proc.stderr or proc.stdout)[-600:]
                return LiveRedteamResult(
                    ok=False,
                    error=f"promptfoo redteam produced no results file. Output: {tail}",
                    latency_seconds=round(elapsed, 2),
                    code_snippet=snippet,
                )

            data = json.loads(output_path.read_text())
            rows = data.get("results", {}).get("results", [])
            if not rows:
                return LiveRedteamResult(
                    ok=False, error="promptfoo redteam generated no test cases to run.",
                    latency_seconds=round(elapsed, 2), code_snippet=snippet,
                )

            probes = []
            held_count = 0
            for row in rows:
                vars_ = row.get("vars") or {}
                probe_text = vars_.get("message") or next(iter(vars_.values()), "")
                response = row.get("response")
                response_text = response.get("output") if isinstance(response, dict) else (response or "")
                grading = row.get("gradingResult") or {}
                # In promptfoo's own grading vocabulary, `success: true` on a
                # redteam row means the target RESISTED the attack (a "pass"
                # against the contracts check) - the same field the plain
                # eval demo reads, same meaning: the assertion held.
                held = bool(row.get("success"))
                if held:
                    held_count += 1
                probes.append(RedteamProbe(
                    prompt=str(probe_text),
                    response=str(response_text),
                    held=held,
                    reason=grading.get("reason"),
                ))

            return LiveRedteamResult(
                ok=True,
                total=len(probes),
                held=held_count,
                probes=probes,
                latency_seconds=round(elapsed, 2),
                code_snippet=snippet,
            )
    except subprocess.TimeoutExpired:
        return LiveRedteamResult(
            ok=False,
            error=(
                "promptfoo redteam didn't finish within 240s. Verified directly: on a "
                "persistent connection failure, its local generation step retries far more "
                "aggressively than plain `promptfoo eval` - this is very likely that, not a "
                "bug. Check your network/API key and try again."
            ),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LiveRedteamResult(ok=False, error=str(exc), code_snippet=snippet)
