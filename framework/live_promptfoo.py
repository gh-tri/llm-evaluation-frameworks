"""
Real, live Promptfoo call behind framework/app.py's Promptfoo page.

This page's demo looks different on purpose too, but for the opposite
reason from Langfuse: Promptfoo isn't a Python library at all - it's a
YAML-configured CLI (`promptfoo eval`). This demo writes a tiny config to
a temp file and shells out to the real `promptfoo` binary, exactly as you
would from a terminal - a genuinely live run, just via a subprocess
instead of a Python import.

It's also the one demo on this whole page where nothing is pre-written:
every other framework here grades an answer you already typed. Promptfoo
actually calls the provider to GENERATE the answer from your prompt
template, then grades it with its own `llm-rubric` assertion type (a
plain-English criteria, Promptfoo's own G-Eval analog) - prompt, live
generation, and grading in one command.

Needs `promptfoo` on PATH (npm install -g promptfoo) and OPENAI_API_KEY.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

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
