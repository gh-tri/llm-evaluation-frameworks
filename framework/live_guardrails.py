"""
Real, live Guardrails AI calls behind framework/app.py's Guardrails AI page.

Two live demos, each showing a genuinely different mechanism from every
other framework on this page - Guardrails doesn't score free text with an
LLM-as-judge rubric; it VALIDATES and ENFORCES:

  #1 Custom validator, live -> the same "define a metric" flow as every
     other framework's demo #1, but here a plain-English criteria becomes
     a custom Validator class (guardrails.validator_base.Validator),
     returning PassResult/FailResult rather than a continuous score.

  #2 Schema-enforced generation, live -> Guard.for_pydantic(...) calls the
     LLM itself (unlike every other demo on this page, which grades a
     pre-written answer) and guarantees the response validates against a
     Pydantic schema - Guardrails' actual headline feature.

Needs OPENAI_API_KEY only, no Guardrails Hub account.

Verified pain point: Guard() unconditionally constructs a HubTelemetry
singleton pointed at a hardcoded Guardrails-owned endpoint
(hty0gc1ok3.execute-api.us-east-1.amazonaws.com), enabled by default
(settings.rc.enable_metrics defaults to True even with no ~/.guardrailsrc
file present). Setting settings.rc.enable_metrics = False in-process stops
new spans from being recorded, but the BatchSpanProcessor/OTLPSpanExporter
are constructed unconditionally regardless, so a background flush attempt
at interpreter shutdown still fires - harmless in a long-running Streamlit
process (fires once at server shutdown, never per-click), but a genuine,
documentable surprise the first time you see an unexpected outbound
connection from a "local" validation library.
"""
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from schema.env_config import check_openai  # noqa: E402

try:
    from guardrails.settings import settings as _gr_settings
    _gr_settings.rc.enable_metrics = False
    _gr_settings.disable_tracing = True
except Exception:
    pass

JUDGE_MODEL_DEFAULT = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Demo #1: a plain-English criteria becomes a custom Validator
# ---------------------------------------------------------------------------
@dataclass
class LiveValidatorResult:
    ok: bool
    passed: Optional[bool] = None
    reason: Optional[str] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def build_validator_code_snippet(criteria: str, model: str) -> str:
    return (
        "from guardrails import Guard\n"
        "from guardrails.validator_base import Validator, register_validator, PassResult, FailResult\n"
        "from guardrails.types.on_fail import OnFailAction\n\n"
        "@register_validator(name='criteria-check', data_type='string')\n"
        "class CriteriaCheck(Validator):\n"
        "    def validate(self, value, metadata):\n"
        f"        # asks {model!r} whether `value` meets: {criteria!r}\n"
        "        ...\n"
        "        return PassResult() if meets_criteria else FailResult(error_message=reason)\n\n"
        "guard = Guard().use(CriteriaCheck(on_fail=OnFailAction.NOOP))\n"
        "outcome = guard.validate(<candidate answer>)\n"
        "outcome.validation_passed  # -> what's shown below\n"
        "# Note: outcome.validation_summaries is only ever populated on a FAIL -\n"
        "# it's empty on a pass, verified directly - so the reason text on a pass\n"
        "# has to be captured inside validate() itself, as this demo does."
    )


def run_custom_validator(
    criteria: str,
    input_text: str,
    actual_output: str,
    model: str = JUDGE_MODEL_DEFAULT,
) -> LiveValidatorResult:
    snippet = build_validator_code_snippet(criteria, model)

    status = check_openai()
    if not status.present:
        return LiveValidatorResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make a real "
                "judge-model call. Add one to .env and rerun."
            ),
            code_snippet=snippet,
        )

    try:
        from guardrails import Guard
        from guardrails.validator_base import Validator, register_validator, PassResult, FailResult
        from guardrails.types.on_fail import OnFailAction
        from openai import OpenAI

        last_reason = {}

        # Re-registering the same name on every Streamlit rerun is safe -
        # register_validator's registry is a plain dict, so this just
        # overwrites the previous entry rather than erroring, verified
        # directly.
        @register_validator(name="criteria-check-live", data_type="string")
        class CriteriaCheck(Validator):
            def validate(self, value, metadata):
                client = OpenAI()
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role": "user",
                        "content": (
                            f"Question: {input_text}\n\nAnswer: {value}\n\n"
                            f"Criteria: {criteria}\n\n"
                            "Does the answer meet the criteria? Respond with exactly two "
                            "lines: the first line Y or N, the second line a one-sentence "
                            "reason."
                        ),
                    }],
                    temperature=0,
                )
                text = (resp.choices[0].message.content or "").strip()
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                decision = lines[0].upper() if lines else "N"
                reason = lines[1] if len(lines) > 1 else text
                last_reason["value"] = reason
                if decision.startswith("Y"):
                    return PassResult(metadata={"reason": reason})
                return FailResult(error_message=reason, metadata={"reason": reason})

        guard = Guard().use(CriteriaCheck(on_fail=OnFailAction.NOOP))

        start = time.monotonic()
        outcome = guard.validate(actual_output)
        elapsed = time.monotonic() - start

        return LiveValidatorResult(
            ok=True,
            passed=outcome.validation_passed,
            reason=last_reason.get("value"),
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LiveValidatorResult(ok=False, error=str(exc), code_snippet=snippet)


# ---------------------------------------------------------------------------
# Demo #2: Guard.for_pydantic - the LLM call itself is schema-enforced
# ---------------------------------------------------------------------------
SCHEMA_CODE = """from pydantic import BaseModel, Field
from typing import Literal

class SupportTriage(BaseModel):
    category: Literal["shipping", "billing", "account", "other"] = Field(
        description="The category of the customer issue"
    )
    urgency: int = Field(description="Urgency from 1 (low) to 5 (high)", ge=1, le=5)
    summary: str = Field(description="One-sentence summary of the issue")"""


@dataclass
class LiveSchemaResult:
    ok: bool
    category: Optional[str] = None
    urgency: Optional[int] = None
    summary: Optional[str] = None
    raw_output: Optional[str] = None
    latency_seconds: Optional[float] = None
    error: Optional[str] = None
    code_snippet: str = ""


def build_schema_code_snippet(model: str) -> str:
    return (
        f"{SCHEMA_CODE}\n\n"
        "from guardrails import Guard\n"
        "guard = Guard.for_pydantic(SupportTriage)\n"
        f"result = guard(model={model!r}, messages=[{{'role': 'user', 'content': <customer message>}}])\n"
        "result.validated_output  # -> guaranteed to match SupportTriage's schema, or a\n"
        "                         #    validation error - never free text"
    )


def run_schema_enforced_generation(
    customer_message: str,
    model: str = JUDGE_MODEL_DEFAULT,
) -> LiveSchemaResult:
    snippet = build_schema_code_snippet(model)

    status = check_openai()
    if not status.present:
        return LiveSchemaResult(
            ok=False,
            error=(
                "No OPENAI_API_KEY set in this environment, so this can't make a real "
                "generation call. Add one to .env and rerun."
            ),
            code_snippet=snippet,
        )

    try:
        from pydantic import BaseModel, Field
        from typing import Literal
        from guardrails import Guard

        class SupportTriage(BaseModel):
            category: Literal["shipping", "billing", "account", "other"] = Field(
                description="The category of the customer issue"
            )
            urgency: int = Field(description="Urgency from 1 (low) to 5 (high)", ge=1, le=5)
            summary: str = Field(description="One-sentence summary of the issue")

        guard = Guard.for_pydantic(SupportTriage)

        start = time.monotonic()
        result = guard(
            model=model,
            messages=[{
                "role": "user",
                "content": f"Extract the triage fields from this customer message:\n\n{customer_message}",
            }],
        )
        elapsed = time.monotonic() - start

        validated = result.validated_output or {}
        get = (lambda k: validated.get(k)) if isinstance(validated, dict) else (lambda k: getattr(validated, k, None))

        return LiveSchemaResult(
            ok=True,
            category=get("category"),
            urgency=get("urgency"),
            summary=get("summary"),
            raw_output=result.raw_llm_output,
            latency_seconds=round(elapsed, 2),
            code_snippet=snippet,
        )
    except Exception as exc:  # noqa: BLE001 - live demo, never crash the page
        return LiveSchemaResult(ok=False, error=str(exc), code_snippet=snippet)
