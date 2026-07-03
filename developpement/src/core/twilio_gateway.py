"""
Twilio voice and Media Streams support for V.O.T. Guardian.

This module keeps Twilio-specific parsing, signature validation, TwiML
generation, and live-stream state outside the Flask route layer. It is designed
for a supervised education workflow: stream metadata and short audio windows
are converted into review artifacts, while raw audio bytes stay in memory and
are wiped after use.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from html import escape
from threading import RLock
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional

try:  # pragma: no cover - exercised when twilio is installed
    from twilio.request_validator import RequestValidator
except Exception:  # pragma: no cover - fallback is covered by unit tests
    RequestValidator = None  # type: ignore[assignment]


SAFE_REVIEW_LABELS = (
    "review required",
    "signal quality concern",
    "uncertain voice-risk indicator",
    "evidence gap",
    "human review needed",
)


class TwilioRequestValidationError(ValueError):
    """Raised when a Twilio webhook signature cannot be validated."""


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_csv(name: str) -> set[str]:
    raw = os.getenv(name, "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def _now_ms() -> int:
    return int(time.time() * 1000)


def redact_phone(value: Optional[str]) -> Optional[str]:
    """Return a minimal phone redaction suitable for logs and APIs."""
    if not value:
        return None
    digits = "".join(char for char in value if char.isdigit())
    if len(digits) <= 2:
        return "**"
    country_hint = "+" if value.startswith("+") else ""
    return f"{country_hint}***{digits[-2:]}"


def redacted_form(form: Mapping[str, Any]) -> Dict[str, Any]:
    """Redact Twilio form fields before storing session metadata."""
    safe: Dict[str, Any] = {}
    phone_keys = {"from", "to", "caller", "called"}
    blocked_keys = {"recordingurl", "body"}

    for key, value in form.items():
        normalized = key.lower()
        if normalized in phone_keys:
            safe[key] = redact_phone(str(value))
        elif normalized in blocked_keys:
            safe[key] = "[redacted]"
        elif normalized.endswith("sid") or normalized in {
            "callstatus",
            "direction",
            "fromcountry",
            "tocountry",
            "fromcity",
            "tocity",
            "digits",
        }:
            safe[key] = value
    return safe


def compute_twilio_signature(
    url: str,
    params: Mapping[str, Any],
    auth_token: str,
) -> str:
    """Compute Twilio's form webhook signature for tests and SDK fallback."""
    payload = url
    for key in sorted(params.keys()):
        payload += f"{key}{params[key]}"
    digest = hmac.new(
        auth_token.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def validate_twilio_signature(
    url: str,
    params: Mapping[str, Any],
    signature: str,
    auth_token: str,
) -> bool:
    """Validate an inbound Twilio form webhook signature."""
    if not auth_token or not signature:
        return False

    if RequestValidator is not None:  # pragma: no cover - optional dependency
        validator = RequestValidator(auth_token)
        return bool(validator.validate(url, dict(params), signature))

    expected = compute_twilio_signature(url, params, auth_token)
    return hmac.compare_digest(expected, signature)


@dataclass
class TwilioGatewayConfig:
    """Runtime configuration for the Twilio gateway."""

    account_sid: str = ""
    auth_token: str = ""
    voice_number: str = ""
    public_base_url: str = "https://example.invalid"
    media_ws_url: str = ""
    validate_signatures: bool = True
    demo_mode: bool = False
    max_media_buffer_bytes: int = 256_000
    max_call_duration_seconds: int = 300
    session_ttl_seconds: int = 900
    allowed_callers: set[str] = field(default_factory=set)

    @classmethod
    def from_env(cls) -> "TwilioGatewayConfig":
        public_base_url = os.getenv(
            "TWILIO_PUBLIC_BASE_URL",
            "https://example.invalid",
        ).rstrip("/")
        media_ws_url = os.getenv("TWILIO_MEDIA_WS_URL", "").strip()
        if not media_ws_url and public_base_url.startswith("https://"):
            media_ws_url = (
                "wss://"
                + public_base_url.removeprefix("https://")
                + "/twilio/media"
            )

        return cls(
            account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
            auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
            voice_number=os.getenv("TWILIO_VOICE_NUMBER", ""),
            public_base_url=public_base_url,
            media_ws_url=media_ws_url or "wss://example.invalid/twilio/media",
            validate_signatures=_env_bool("TWILIO_VALIDATE_SIGNATURES", True),
            demo_mode=_env_bool("TWILIO_DEMO_MODE", False),
            max_media_buffer_bytes=int(
                os.getenv("TWILIO_MAX_MEDIA_BUFFER_BYTES", "256000")
            ),
            max_call_duration_seconds=int(
                os.getenv("TWILIO_MAX_CALL_DURATION_SECONDS", "300")
            ),
            session_ttl_seconds=int(os.getenv("TWILIO_SESSION_TTL_SECONDS", "900")),
            allowed_callers=_env_csv("TWILIO_ALLOWED_CALLERS"),
        )

    def public_action_url(self) -> str:
        return f"{self.public_base_url}/twilio/voice"


class TwilioSessionStore:
    """Thread-safe in-memory session store for live call review state."""

    def __init__(self, ttl_seconds: int = 900):
        self.ttl_seconds = ttl_seconds
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def create(
        self,
        call_sid: str,
        metadata: Mapping[str, Any],
    ) -> Dict[str, Any]:
        self.prune()
        session_id = f"twilio_{uuid.uuid4().hex}"
        session = {
            "session_id": session_id,
            "call_sid": call_sid,
            "status": "awaiting_consent",
            "created_at_ms": _now_ms(),
            "updated_at_ms": _now_ms(),
            "expires_at_ms": _now_ms() + self.ttl_seconds * 1000,
            "frames_received": 0,
            "bytes_received": 0,
            "raw_audio_retained": False,
            "review_state": "human review needed",
            "review_artifacts": [],
            "timeline": [],
            "metadata": dict(metadata),
            "errors": [],
        }
        with self._lock:
            self._sessions[session_id] = session
        self.add_timeline(session_id, "session_created")
        return self.get(session_id) or session

    def find_by_call_sid(self, call_sid: str) -> Optional[Dict[str, Any]]:
        self.prune()
        with self._lock:
            for session in self._sessions.values():
                if session.get("call_sid") == call_sid:
                    return json.loads(json.dumps(session))
        return None

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        self.prune()
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            return json.loads(json.dumps(session))

    def update(self, session_id: str, **changes: Any) -> Optional[Dict[str, Any]]:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            session.update(changes)
            session["updated_at_ms"] = _now_ms()
            return json.loads(json.dumps(session))

    def add_timeline(
        self,
        session_id: str,
        event: str,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return
            session["timeline"].append(
                {
                    "event": event,
                    "at_ms": _now_ms(),
                    "metadata": dict(metadata or {}),
                }
            )
            session["updated_at_ms"] = _now_ms()

    def add_artifact(self, session_id: str, artifact: Mapping[str, Any]) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return
            session["review_artifacts"].append(dict(artifact))
            session["review_artifacts"] = session["review_artifacts"][-20:]
            session["review_state"] = artifact.get(
                "label",
                session.get("review_state", "human review needed"),
            )
            session["updated_at_ms"] = _now_ms()

    def add_error(self, session_id: str, error: str) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return
            session["errors"].append({"message": error, "at_ms": _now_ms()})
            session["status"] = "error"
            session["updated_at_ms"] = _now_ms()

    def prune(self) -> None:
        now = _now_ms()
        with self._lock:
            expired = [
                session_id
                for session_id, session in self._sessions.items()
                if session.get("expires_at_ms", 0) < now
            ]
            for session_id in expired:
                del self._sessions[session_id]


class TwilioMediaStreamProcessor:
    """Parse Twilio Media Stream events into bounded review artifacts."""

    def __init__(self, store: TwilioSessionStore, config: TwilioGatewayConfig):
        self.store = store
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._buffers: Dict[str, bytearray] = {}
        self._lock = RLock()

    def handle_event(
        self,
        session_id: str,
        event: Mapping[str, Any],
    ) -> Dict[str, Any]:
        event_type = str(event.get("event", "unknown"))

        handlers = {
            "connected": self._handle_connected,
            "start": self._handle_start,
            "media": self._handle_media,
            "stop": self._handle_stop,
        }
        handler = handlers.get(event_type)
        if handler is None:
            self.store.add_error(session_id, f"Unsupported stream event: {event_type}")
            return {
                "accepted": False,
                "event": event_type,
                "label": "evidence gap",
            }
        return handler(session_id, event)

    def _handle_connected(
        self,
        session_id: str,
        event: Mapping[str, Any],
    ) -> Dict[str, Any]:
        self.store.update(session_id, status="stream_connected")
        self.store.add_timeline(session_id, "stream_connected")
        return {"accepted": True, "event": "connected"}

    def _handle_start(
        self,
        session_id: str,
        event: Mapping[str, Any],
    ) -> Dict[str, Any]:
        start = event.get("start") or {}
        if not isinstance(start, Mapping):
            start = {}
        stream_sid = str(start.get("streamSid") or event.get("streamSid") or "")
        custom_parameters = start.get("customParameters") or {}
        if not isinstance(custom_parameters, Mapping):
            custom_parameters = {}
        self.store.update(
            session_id,
            status="streaming",
            stream_sid=stream_sid,
            stream_parameters={
                key: str(value)
                for key, value in custom_parameters.items()
                if key in {"session_id", "review_mode", "retention"}
            },
        )
        self.store.add_timeline(session_id, "stream_started")
        return {"accepted": True, "event": "start", "stream_sid": stream_sid}

    def _handle_media(
        self,
        session_id: str,
        event: Mapping[str, Any],
    ) -> Dict[str, Any]:
        media = event.get("media") or {}
        if not isinstance(media, Mapping):
            self.store.add_error(session_id, "Malformed media event")
            return {"accepted": False, "event": "media", "label": "evidence gap"}

        payload = str(media.get("payload") or "")
        try:
            frame = base64.b64decode(payload, validate=True)
        except Exception:
            self.store.add_error(session_id, "Invalid base64 media payload")
            return {"accepted": False, "event": "media", "label": "evidence gap"}

        with self._lock:
            buffer = self._buffers.setdefault(session_id, bytearray())
            if len(buffer) + len(frame) > self.config.max_media_buffer_bytes:
                self._zero_buffer(session_id)
                self.store.add_error(session_id, "Media buffer limit exceeded")
                return {
                    "accepted": False,
                    "event": "media",
                    "label": "evidence gap",
                }
            buffer.extend(frame)

        session = self.store.get(session_id)
        frames = int((session or {}).get("frames_received", 0)) + 1
        byte_count = int((session or {}).get("bytes_received", 0)) + len(frame)
        artifact = self._artifact_from_frame(frame, frames, byte_count)

        self.store.update(
            session_id,
            status="streaming",
            frames_received=frames,
            bytes_received=byte_count,
            raw_audio_retained=False,
        )
        self.store.add_artifact(session_id, artifact)
        self.store.add_timeline(
            session_id,
            "media_frame_reviewed",
            {"frames_received": frames, "bytes_received": byte_count},
        )
        self._zero_buffer(session_id)
        return {"accepted": True, "event": "media", "artifact": artifact}

    def _handle_stop(
        self,
        session_id: str,
        event: Mapping[str, Any],
    ) -> Dict[str, Any]:
        self._zero_buffer(session_id)
        artifact = {
            "label": "human review needed",
            "summary": "Stream closed; reviewer must inspect context and consent record.",
            "confidence": 0.0,
            "evidence_gap": "Live call stream ended; no raw audio was retained.",
            "at_ms": _now_ms(),
        }
        self.store.update(session_id, status="manual_review", raw_audio_retained=False)
        self.store.add_artifact(session_id, artifact)
        self.store.add_timeline(session_id, "stream_stopped")
        return {"accepted": True, "event": "stop", "artifact": artifact}

    def _artifact_from_frame(
        self,
        frame: bytes,
        frames_received: int,
        bytes_received: int,
    ) -> Dict[str, Any]:
        label = "review required"
        evidence_gap = "Short live stream window only; not enough evidence for a conclusion."
        if not frame:
            label = "evidence gap"
            evidence_gap = "Empty media frame received."
        elif len(frame) < 80:
            label = "signal quality concern"
            evidence_gap = "Frame is too small for stable review."

        return {
            "label": label,
            "allowed_labels": list(SAFE_REVIEW_LABELS),
            "summary": "Live voice-risk review artifact generated for supervised review.",
            "confidence": 0.0,
            "frames_received": frames_received,
            "bytes_received": bytes_received,
            "evidence_gap": evidence_gap,
            "raw_audio_retained": False,
            "at_ms": _now_ms(),
        }

    def _zero_buffer(self, session_id: str) -> None:
        with self._lock:
            buffer = self._buffers.pop(session_id, None)
            if buffer is None:
                return
            for index in range(len(buffer)):
                buffer[index] = 0


class TwilioGateway:
    """High-level Twilio gateway facade used by Flask routes."""

    def __init__(self, config: Optional[TwilioGatewayConfig] = None):
        self.config = config or TwilioGatewayConfig.from_env()
        self.store = TwilioSessionStore(self.config.session_ttl_seconds)
        self.media_processor = TwilioMediaStreamProcessor(self.store, self.config)
        self.logger = logging.getLogger(__name__)

    def validate_request(
        self,
        url: str,
        params: Mapping[str, Any],
        signature: str,
    ) -> None:
        if self.config.demo_mode or not self.config.validate_signatures:
            return
        if not self.config.auth_token:
            raise TwilioRequestValidationError(
                "TWILIO_AUTH_TOKEN is required when signature validation is enabled"
            )
        if not validate_twilio_signature(
            url=url,
            params=params,
            signature=signature,
            auth_token=self.config.auth_token,
        ):
            raise TwilioRequestValidationError("Invalid Twilio signature")

    def create_or_get_voice_session(
        self,
        form: Mapping[str, Any],
    ) -> Dict[str, Any]:
        call_sid = str(form.get("CallSid") or f"call_{uuid.uuid4().hex}")
        existing = self.store.find_by_call_sid(call_sid)
        if existing:
            return existing

        caller = str(form.get("From") or "")
        if self.config.allowed_callers and caller not in self.config.allowed_callers:
            session = self.store.create(call_sid, redacted_form(form))
            self.store.update(session["session_id"], status="blocked")
            self.store.add_error(session["session_id"], "Caller not allowed")
            return self.store.get(session["session_id"]) or session

        return self.store.create(call_sid, redacted_form(form))

    def build_voice_response(self, form: Mapping[str, Any]) -> tuple[str, Dict[str, Any]]:
        session = self.create_or_get_voice_session(form)
        digit = str(form.get("Digits") or "")

        if session.get("status") == "blocked":
            return self._hangup_twiml(
                "This V.O.T Guardian pilot is limited to approved test callers."
            ), session

        if digit == "1":
            self.store.update(session["session_id"], status="consented")
            self.store.add_timeline(session["session_id"], "consent_confirmed")
            return self._stream_twiml(session), self.store.get(session["session_id"]) or session

        if digit and digit != "1":
            self.store.update(session["session_id"], status="consent_declined")
            self.store.add_timeline(session["session_id"], "consent_declined")
            return self._hangup_twiml(
                "Consent was not confirmed. The session is closed."
            ), session

        return self._consent_twiml(), session

    def handle_media_event(
        self,
        event: Mapping[str, Any],
        fallback_session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        session_id = self._session_id_from_event(event) or fallback_session_id
        if not session_id:
            return {"accepted": False, "label": "evidence gap", "error": "session_id missing"}
        if not self.store.get(session_id):
            return {"accepted": False, "label": "evidence gap", "error": "session not found"}
        return self.media_processor.handle_event(session_id, event)

    def _session_id_from_event(self, event: Mapping[str, Any]) -> Optional[str]:
        start = event.get("start")
        if isinstance(start, Mapping):
            custom_parameters = start.get("customParameters")
            if isinstance(custom_parameters, Mapping):
                session_id = custom_parameters.get("session_id")
                if session_id:
                    return str(session_id)
        return None

    def _consent_twiml(self) -> str:
        action = escape(self.config.public_action_url(), quote=True)
        prompt_en = (
            "V.O.T Guardian is a supervised educational voice risk review pilot. "
            "Audio is streamed for review signals only, raw audio is not retained, "
            "and a human reviewer must inspect any result. Press 1 to continue."
        )
        prompt_fr = (
            "V.O.T Guardian est un pilote educatif supervise. "
            "Appuyez sur 1 pour continuer, ou raccrochez pour refuser."
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            f'<Gather numDigits="1" action="{action}" method="POST" timeout="8">'
            f'<Say language="en-US">{escape(prompt_en)}</Say>'
            f'<Say language="fr-CA">{escape(prompt_fr)}</Say>'
            "</Gather>"
            "<Say>No consent was received. The session is closed.</Say>"
            "<Hangup/>"
            "</Response>"
        )

    def _stream_twiml(self, session: Mapping[str, Any]) -> str:
        stream_url = escape(self.config.media_ws_url, quote=True)
        session_id = escape(str(session["session_id"]), quote=True)
        call_sid = escape(str(session.get("call_sid") or ""), quote=True)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            "<Start>"
            f'<Stream name="vot-guardian-review" url="{stream_url}">'
            f'<Parameter name="session_id" value="{session_id}"/>'
            f'<Parameter name="call_sid" value="{call_sid}"/>'
            '<Parameter name="review_mode" value="supervised"/>'
            '<Parameter name="retention" value="no_raw_audio"/>'
            "</Stream>"
            "</Start>"
            "<Say>Streaming is active for supervised review. "
            "No autonomous decision will be made.</Say>"
            f'<Pause length="{min(self.config.max_call_duration_seconds, 60)}"/>'
            "<Say>The review window is complete. A human review is required.</Say>"
            "<Hangup/>"
            "</Response>"
        )

    def _hangup_twiml(self, message: str) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            f"<Say>{escape(message)}</Say>"
            "<Hangup/>"
            "</Response>"
        )


def parse_json_event(raw_message: str) -> Dict[str, Any]:
    """Parse a Twilio Media Stream JSON event."""
    decoded = json.loads(raw_message)
    if not isinstance(decoded, MutableMapping):
        raise ValueError("Media Stream event must be a JSON object")
    return dict(decoded)


def form_mapping(values: Mapping[str, Any]) -> Dict[str, str]:
    """Normalize Flask form/query values into a plain string mapping."""
    normalized: Dict[str, str] = {}
    for key, value in values.items():
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            normalized[key] = str(list(value)[0])
        else:
            normalized[key] = str(value)
    return normalized
