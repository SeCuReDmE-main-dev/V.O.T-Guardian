"""Tests for Twilio Voice and Media Streams gateway behavior."""

import base64

from src.core.twilio_gateway import (
    TwilioGateway,
    TwilioGatewayConfig,
    compute_twilio_signature,
    validate_twilio_signature,
)


def _gateway() -> TwilioGateway:
    return TwilioGateway(
        TwilioGatewayConfig(
            auth_token="test-token",
            public_base_url="https://vot.example.test",
            media_ws_url="wss://vot.example.test/twilio/media",
            validate_signatures=True,
            max_media_buffer_bytes=1024,
        )
    )


def test_signature_validation_accepts_signed_form_payload():
    url = "https://vot.example.test/twilio/voice"
    params = {"CallSid": "CA123", "From": "+15145550123", "To": "+15145550999"}
    signature = compute_twilio_signature(url, params, "test-token")

    assert validate_twilio_signature(url, params, signature, "test-token")


def test_signature_validation_rejects_invalid_signature():
    url = "https://vot.example.test/twilio/voice"
    params = {"CallSid": "CA123"}

    assert not validate_twilio_signature(url, params, "bad-signature", "test-token")


def test_voice_response_starts_with_consent_gather():
    gateway = _gateway()
    twiml, session = gateway.build_voice_response({
        "CallSid": "CA123",
        "From": "+15145550123",
        "To": "+15145550999",
    })

    assert session["status"] == "awaiting_consent"
    assert "<Gather" in twiml
    assert "Press 1 to continue" in twiml
    assert "no raw audio is not retained" not in twiml
    assert "+15145550123" not in twiml


def test_voice_response_streams_after_digit_consent_without_pii_params():
    gateway = _gateway()
    gateway.build_voice_response({"CallSid": "CA123", "From": "+15145550123"})
    twiml, session = gateway.build_voice_response({
        "CallSid": "CA123",
        "From": "+15145550123",
        "Digits": "1",
    })

    assert session["status"] in {"consented", "awaiting_consent"}
    assert "<Stream" in twiml
    assert 'url="wss://vot.example.test/twilio/media"' in twiml
    assert 'name="session_id"' in twiml
    assert 'value="no_raw_audio"' in twiml
    assert "+15145550123" not in twiml


def test_media_events_create_review_artifacts_and_drop_raw_audio():
    gateway = _gateway()
    session = gateway.store.create("CA123", {"From": "***23"})
    session_id = session["session_id"]

    connected = gateway.handle_media_event({"event": "connected"}, session_id)
    start = gateway.handle_media_event({
        "event": "start",
        "start": {
            "streamSid": "MZ123",
            "customParameters": {"session_id": session_id},
        },
    })
    media = gateway.handle_media_event({
        "event": "media",
        "media": {
            "payload": base64.b64encode(b"\xff" * 160).decode("ascii"),
        },
    }, session_id)
    stop = gateway.handle_media_event({"event": "stop"}, session_id)

    assert connected["accepted"]
    assert start["accepted"]
    assert media["accepted"]
    assert stop["accepted"]

    updated = gateway.store.get(session_id)
    assert updated is not None
    assert updated["frames_received"] == 1
    assert updated["bytes_received"] == 160
    assert updated["raw_audio_retained"] is False
    assert updated["review_artifacts"][-1]["label"] == "human review needed"


def test_media_event_rejects_unknown_event_safely():
    gateway = _gateway()
    session = gateway.store.create("CA123", {})

    result = gateway.handle_media_event(
        {"event": "unexpected"},
        session["session_id"],
    )

    assert not result["accepted"]
    assert result["label"] == "evidence gap"
