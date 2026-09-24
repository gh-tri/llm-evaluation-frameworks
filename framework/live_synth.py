"""
The real, live DeepEval Synthesizer call behind the second "live" section
in app.py. Same spirit as live_deepeval.py: no mocks, no pre-computed
goldens. The presenter types a one-line scenario and task description -
no dataset, no context chunks - and DeepEval's `generate_goldens_from_scratch`
invents plausible test cases (input + expected_output pairs) from that
description alone, via a real judge-model call.

This is deliberately the "dataset isn't the point" demo: it directly
answers the earlier worry about needing a curated dataset to make a
framework look good - here, DeepEval builds its own.
"""
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from schema.env_config import check_openai  # noqa: E402

JUDGE_MODEL_DEFAULT = "gpt-4o-mini"


@dataclass
class Golden:
    input: str
    expected_output: Optional[str]


@dataclass
class LiveSynthResult:
    ok: bool
    goldens: List[Golden] = field(default_factory=list)
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def build_code_snippet(scenario: str, task: str, input_format: str, num_goldens: int, model: str) -> str:
    return (
        "from deepeval.synthesizer import Synthesizer\n"
        "from deepeval.synthesizer.config import StylingConfig\n\n"
        "styling = StylingConfig(\n"
        f"    scenario={scenario!r},\n"
        f"    task={task!r},\n"
        f"    input_format={input_format!r},\n"
        ")\n"
        f"synthesizer = Synthesizer(model={model!r}, styling_config=styling)\n"
        f"goldens = synthesizer.generate_goldens_from_scratch(num_goldens={num_goldens})\n"
        "for g in goldens:\n"
        "    g.input, g.expected_output  # -> what's shown below, invented from scratch"
    )


def run_synthesis(
    scenario: str,
    task: str,
    input_format: str,
    num_goldens: int = 3,
    model: str = JUDGE_MODEL_DEFAULT,
) -> LiveSynthResult:
    snippet = build_code_snippet(scenario, task, input_format, num_goldens, model)

    status = check_openai()
    if not status.present:
        return LiveSynthResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make a real "
                "generation call. Add one to .env and rerun - this demo's whole point is "
                "that the test cases below don't exist until a real call invents them."
            ),
            code_snippet=snippet,
        )

    try:
        from deepeval.synthesizer import Synthesizer
        from deepeval.synthesizer.config import StylingConfig

        styling = StylingConfig(scenario=scenario, task=task, input_format=input_format)
        synthesizer = Synthesizer(model=model, styling_config=styling)

        start = time.monotonic()
        raw_goldens = synthesizer.generate_goldens_from_scratch(num_goldens=num_goldens)
        elapsed = time.monotonic() - start

        goldens = [Golden(input=g.input, expected_output=g.expected_output) for g in raw_goldens]

        return LiveSynthResult(
            ok=True,
            goldens=goldens,
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live, presenter-facing: any failure
        # (rate limit, timeout, bad key) should show up as a clear message on stage,
        # never a crashed Streamlit page.
        return LiveSynthResult(ok=False, error=str(exc), code_snippet=snippet)
