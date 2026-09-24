"""
Real, live Garak call behind framework/app.py's Garak page.

The most different demo on this whole page: Garak isn't a scoring
framework at all - it's a red-team scanner. There's no "define a metric"
moment here because Garak doesn't grade an answer you already wrote; it
attacks a live model with adversarial prompts and checks whether the
attack succeeded. This demo shells out to the real `garak` CLI (a
subprocess, like Promptfoo) and runs one small, safe, real probe against
a real model.

The probe: goodside.WhoIsRiley (6 prompts, ~1-6s each depending on
generations) paired with its own detector, goodside.RileyIsnt - it checks
whether the model confidently hallucinates false biographical "facts"
about an obscure real person (being Canadian, a singer, etc.) rather than
admitting uncertainty. Picked deliberately small and workplace-safe out
of garak's hundreds of probes - many other probes are 50-200+ prompts, or
pair with `always.Fail` (a deprecated placeholder detector that always
reports "vulnerable" regardless of what the model actually said, which
would make for a live demo that never discriminates) rather than a real
semantic check.

Needs the `garak` package importable (pip install garak) and
OPENAI_API_KEY - garak's own openai generator reads it directly.
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
PROBE = "goodside.WhoIsRiley"
DETECTOR = "goodside.RileyIsnt"
GOAL = "get misinfo about riley goodside"


def check_garak() -> bool:
    return shutil.which("garak") is not None or _garak_importable()


def _garak_importable() -> bool:
    try:
        import garak  # noqa: F401
        return True
    except ImportError:
        return False


@dataclass
class GarakExample:
    prompt: str
    output: str
    passed: bool


@dataclass
class LiveGarakResult:
    ok: bool
    passed: Optional[int] = None
    total: Optional[int] = None
    examples: List[GarakExample] = field(default_factory=list)
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def build_code_snippet(model: str, generations: int) -> str:
    return (
        f"python -m garak --model_type openai --model_name {model} \\\n"
        f"    --probes {PROBE} --generations {generations} \\\n"
        "    --report_prefix /tmp/garak_run\n\n"
        f"# {PROBE} sends 6 adversarial prompts asking who Riley Goodside is;\n"
        f"# {DETECTOR} checks each response for fabricated details\n"
        "# (Canadian, female pronouns, being a singer) rather than admitted uncertainty"
    )


def run_probe(model: str = JUDGE_MODEL_DEFAULT, generations: int = 1) -> LiveGarakResult:
    snippet = build_code_snippet(model, generations)

    status = check_openai()
    if not status.present:
        return LiveGarakResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so garak's openai generator "
                "can't call a real model. Add one to .env and rerun."
            ),
            code_snippet=snippet,
        )

    if not check_garak():
        return LiveGarakResult(
            ok=False,
            error="The `garak` package isn't installed in this environment. Install with `pip install garak` and rerun.",
            code_snippet=snippet,
        )

    try:
        with tempfile.TemporaryDirectory() as tmp:
            report_prefix = str(Path(tmp) / "garak_run")

            start = time.monotonic()
            proc = subprocess.run(
                [sys.executable, "-m", "garak",
                 "--model_type", "openai", "--model_name", model,
                 "--probes", PROBE, "--generations", str(generations),
                 "--report_prefix", report_prefix],
                cwd=tmp, env=dict(os.environ), capture_output=True, text=True, timeout=180,
            )
            elapsed = time.monotonic() - start

            report_path = Path(f"{report_prefix}.report.jsonl")
            if not report_path.exists():
                return LiveGarakResult(
                    ok=False,
                    error=f"garak produced no report. stderr: {proc.stderr[-500:]}",
                    latency_seconds=round(elapsed, 2),
                    code_snippet=snippet,
                )

            eval_entry = None
            attempts_by_seq = {}
            for line in report_path.read_text().splitlines():
                entry = json.loads(line)
                if entry.get("entry_type") == "eval":
                    eval_entry = entry
                elif entry.get("entry_type") == "attempt":
                    # garak writes each attempt twice: once right after generation
                    # (detector_results empty) and again after detection runs
                    # (detector_results filled in) - later entries for the same
                    # seq overwrite earlier ones, so this naturally keeps the
                    # final, fully-scored version of each.
                    attempts_by_seq[entry["seq"]] = entry

            if eval_entry is None:
                return LiveGarakResult(
                    ok=False, error="garak's report had no eval summary - the run likely failed outright.",
                    latency_seconds=round(elapsed, 2), code_snippet=snippet,
                )

            examples = []
            for _, attempt in sorted(attempts_by_seq.items())[:3]:
                prompt_text = attempt["prompt"]["turns"][0]["content"]["text"]
                outputs = attempt.get("outputs") or []
                output_text = outputs[0]["text"] if outputs and isinstance(outputs[0], dict) else ""
                detector_scores = (attempt.get("detector_results") or {}).get(DETECTOR, [])
                passed = bool(detector_scores) and detector_scores[0] == 0.0
                examples.append(GarakExample(prompt=prompt_text, output=output_text, passed=passed))

            return LiveGarakResult(
                ok=True,
                passed=eval_entry.get("passed"),
                total=eval_entry.get("total_evaluated"),
                examples=examples,
                latency_seconds=round(elapsed, 2),
                code_snippet=snippet,
            )
    except subprocess.TimeoutExpired:
        return LiveGarakResult(
            ok=False,
            error="garak didn't finish within 180s - likely a provider retry loop; try again.",
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LiveGarakResult(ok=False, error=str(exc), code_snippet=snippet)
