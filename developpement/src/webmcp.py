"""Bounded WebMCP registry for the V.O.T Guardian review prototype.

No tool returns a synthetic voice classification. Audio-derived operations fail
closed until the application supplies an admitted asset resolver and a trained
model runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .config.settings import Settings
from .core.ml.predictor import ModelConfig

SCHEMA = "securedme.webmcp.v1"
PRODUCT = "vot-guardian"


def _property_schema(name: str) -> dict[str, object]:
    if name == "approval":
        return {"type": "object"}
    return {"type": "string", "minLength": 1, "maxLength": 4096}


@dataclass(frozen=True)
class Tool:
    name: str
    effect: str
    description: str
    required: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    available: bool = True

    def descriptor(self) -> dict[str, object]:
        return {"name": self.name, "mode": self.effect, "effect": self.effect, "description": self.description, "inputSchema": {"type": "object", "properties": {name: _property_schema(name) for name in (*self.required, *self.optional)}, "required": list(self.required), "additionalProperties": False}, "outputSchema": {"type": "object"}, "availability": "available" if self.available else "unavailable", "handler": {"kind": "python" if self.available else "unavailable", "module": "src.webmcp"}, **({} if self.available else {"unavailableReason": "Admitted asset resolver and verified local runtime are not configured."})}


DOMAIN_TOOLS = (
    Tool("vot_inspect_service_health", "READ", "Inspect configured capabilities without returning secrets."),
    Tool("vot_inspect_audio_metadata", "EXECUTE", "Inspect metadata for an explicitly admitted ephemeral audio asset.", ("assetRef", "approval", "idempotencyKey"), available=False),
    Tool("vot_extract_voice_review_features", "EXECUTE", "Extract bounded review features from an admitted asset without retention.", ("assetRef", "approval", "idempotencyKey"), available=False),
    Tool("vot_stage_voice_risk_review", "STAGE", "Stage a non-accusatory human review from verified feature output.", ("featureReceiptRef",)),
    Tool("vot_inspect_model_readiness", "READ", "Report whether the trained model checkpoint and runtime are configured."),
    Tool("vot_prepare_twilio_consent_response", "STAGE", "Prepare a consent-first Twilio response without placing a call.", ("sessionRef",)),
    Tool("vot_replay_twilio_media_event", "EXECUTE", "Replay an approved synthetic media event in the configured local service.", ("fixtureRef", "approval", "idempotencyKey"), available=False),
    Tool("vot_inspect_twilio_review_session", "READ", "Inspect a sanitized local review-session projection.", ("sessionRef",)),
    Tool("vot_validate_education_artifact_pointer", "READ", "Validate an opaque education artifact reference.", ("artifactRef",)),
    Tool("vot_build_guardian_protection_plan", "STAGE", "Stage a defensive media-literacy protection plan.", ("scenario",)),
)
COMMON_TOOLS = (
    Tool("securedme_companion_context", "READ", "Return a sanitized V.O.T specialist projection."),
    Tool("securedme_qbit_plan_handoff", "STAGE", "Prepare a Qbit return proposal without changing progression.", ("missionRef", "summary")),
)
TOOLS = DOMAIN_TOOLS + COMMON_TOOLS


def manifest() -> dict[str, object]:
    return {"schema": SCHEMA, "product": {"slug": PRODUCT, "canonicalStateOwner": "algoquest"}, "slug": PRODUCT, "canonicalStateOwner": "algoquest", "tools": [tool.descriptor() for tool in TOOLS], "boundaries": {"authority": "Human review owns every media decision.", "secrets": "No provider credentials or raw audio are returned.", "externalWrites": "Unavailable execution capabilities fail closed.", "heroProgression": "AlgoQuest alone owns Hero Book progression.", "syntheticClassifications": False, "impersonation": False, "surveillance": False, "rawAudioRetention": False, "liveTelephonyByDefault": False}, "theme": {"source": "assets/landing/secureme.ca-product/education/V.O.T Guardian/desing/stitch_v.o.t_guardian_preview_portal/stitch_v.o.t_guardian_preview_portal/tenebris_cyber_safety_logic/DESIGN.md", "sourceStatus": "verified_stitch"}}


def _health(_: Mapping[str, Any]) -> dict[str, object]:
    settings = Settings()
    model = ModelConfig(model_path=settings.ml_model_path, confidence_threshold=settings.ml_confidence_threshold)
    return {
        "status": "degraded" if not Path(model.model_path).is_file() else "configured",
        "modelCheckpointConfigured": Path(model.model_path).is_file(),
        "audioRuntimeRequired": True,
        "twilioConfigured": bool(settings.twilio_account_sid and settings.twilio_auth_token),
        "apiSecretConfigured": bool(settings.api_secret_key),
        "secretsReturned": False,
    }


def _model(_: Mapping[str, Any]) -> dict[str, object]:
    health = _health({})
    return {"ready": health["modelCheckpointConfigured"], "checkpoint": "configured" if health["modelCheckpointConfigured"] else "missing", "randomWeightsAllowed": False, "fallbackClassificationAllowed": False}


def _runtime_disabled(_: Mapping[str, Any]) -> dict[str, object]:
    raise RuntimeError("RUNTIME_NOT_CONFIGURED: admitted asset resolver and verified local runtime are required")


def _stage_review(payload: Mapping[str, Any]) -> dict[str, object]:
    reference = payload.get("featureReceiptRef")
    if not isinstance(reference, str) or not reference.startswith("receipt:"):
        raise ValueError("featureReceiptRef must be an opaque receipt reference")
    return {"status": "staged", "featureReceiptRef": reference, "classification": "UNDETERMINED", "humanReviewRequired": True, "accusation": False, "durableWrite": False}


def _consent(payload: Mapping[str, Any]) -> dict[str, object]:
    if not payload.get("sessionRef"):
        raise ValueError("sessionRef is required")
    return {"status": "staged", "sessionRef": payload["sessionRef"], "message": "Audio review requires explicit participant consent before any media is processed.", "callPlaced": False, "mediaCaptured": False}


def _session(payload: Mapping[str, Any]) -> dict[str, object]:
    reference = payload.get("sessionRef")
    if not isinstance(reference, str) or not reference.startswith("session:"):
        raise ValueError("sessionRef must be an opaque session reference")
    return {"sessionRef": reference, "status": "not_connected", "rawAudioRetained": False, "personalDataReturned": False}


def _artifact(payload: Mapping[str, Any]) -> dict[str, object]:
    reference = payload.get("artifactRef")
    valid = isinstance(reference, str) and reference.startswith("artifact:") and len(reference) <= 200
    return {"valid": valid, "artifactRef": reference if valid else None, "opaque": True}


def _plan(payload: Mapping[str, Any]) -> dict[str, object]:
    scenario = payload.get("scenario")
    if not isinstance(scenario, str) or not scenario.strip():
        raise ValueError("scenario is required")
    return {"status": "staged", "scenario": scenario, "steps": ["obtain explicit consent", "use an admitted fixture or media asset", "inspect uncertainty", "request human review", "delete raw media"], "surveillance": False, "humanReviewRequired": True}


def _handoff(payload: Mapping[str, Any]) -> dict[str, object]:
    if not payload.get("missionRef") or not payload.get("summary"):
        raise ValueError("missionRef and summary are required")
    return {"status": "staged", "missionRef": payload["missionRef"], "summary": payload["summary"], "progressChanged": False, "nextAction": "return_to_qbit_for_human_review"}


HANDLERS: dict[str, Callable[[Mapping[str, Any]], object]] = {
    "vot_inspect_service_health": _health,
    "vot_inspect_audio_metadata": _runtime_disabled,
    "vot_extract_voice_review_features": _runtime_disabled,
    "vot_stage_voice_risk_review": _stage_review,
    "vot_inspect_model_readiness": _model,
    "vot_prepare_twilio_consent_response": _consent,
    "vot_replay_twilio_media_event": _runtime_disabled,
    "vot_inspect_twilio_review_session": _session,
    "vot_validate_education_artifact_pointer": _artifact,
    "vot_build_guardian_protection_plan": _plan,
    "securedme_companion_context": lambda p: {"schema": "HeroBookPanelState.projection.v1", "product": PRODUCT, "specialist": "Neutro", "persona": "defensive voice media review guide", "canonicalStateOwner": "algoquest", "sanitized": True},
    "securedme_qbit_plan_handoff": _handoff,
}


def invoke(name: str, payload: Mapping[str, Any] | None = None) -> dict[str, object]:
    if name not in HANDLERS:
        return {"ok": False, "error": {"code": "TOOL_NOT_ALLOWED", "message": "Unknown V.O.T Guardian tool."}}
    try:
        value = HANDLERS[name](payload or {})
    except RuntimeError as exc:
        code, _, message = str(exc).partition(":")
        return {"ok": False, "error": {"code": code, "message": message.strip()}}
    except (KeyError, TypeError, ValueError) as exc:
        return {"ok": False, "error": {"code": "INVALID_INPUT", "message": str(exc)}}
    return {"ok": True, "tool": name, "result": value, "trace": {"product": PRODUCT, "sanitized": True}}
