"""Flask route tests for Twilio webhook surfaces."""

import base64

import pytest

from src.api import main as api_main
from src.core.twilio_gateway import (
    TwilioGateway,
    TwilioGatewayConfig,
    compute_twilio_signature,
)


@pytest.fixture()
def twilio_client(monkeypatch):
    gateway = TwilioGateway(
        TwilioGatewayConfig(
            auth_token="test-token",
            public_base_url="https://vot.example.test",
            media_ws_url="wss://vot.example.test/twilio/media",
            validate_signatures=True,
            max_media_buffer_bytes=1024,
        )
    )
    monkeypatch.setattr(api_main, "twilio_gateway", gateway)
    return api_main.app.test_client(), gateway


def _signed_headers(url: str, data: dict[str, str]) -> dict[str, str]:
    signature = compute_twilio_signature(url, data, "test-token")
    return {"X-Twilio-Signature": signature}


def test_twilio_voice_rejects_invalid_signature(twilio_client):
    client, _gateway = twilio_client

    response = client.post(
        "/twilio/voice",
        data={"CallSid": "CA123"},
        headers={"X-Twilio-Signature": "bad"},
    )

    assert response.status_code == 403


def test_twilio_voice_returns_consent_twiml_for_signed_call(twilio_client):
    client, gateway = twilio_client
    data = {"CallSid": "CA123", "From": "+15145550123", "To": "+15145550999"}
    url = "http://localhost/twilio/voice"

    response = client.post(
        "/twilio/voice",
        data=data,
        headers=_signed_headers(url, data),
    )

    assert response.status_code == 200
    assert response.mimetype == "text/xml"
    body = response.get_data(as_text=True)
    assert "<Gather" in body
    assert "Press 1 to continue" in body
    assert "+15145550123" not in body
    assert gateway.store.find_by_call_sid("CA123") is not None


def test_twilio_voice_returns_stream_twiml_after_consent(twilio_client):
    client, _gateway = twilio_client
    initial = {"CallSid": "CA123", "From": "+15145550123"}
    consent = {"CallSid": "CA123", "From": "+15145550123", "Digits": "1"}

    client.post(
        "/twilio/voice",
        data=initial,
        headers=_signed_headers("http://localhost/twilio/voice", initial),
    )
    response = client.post(
        "/twilio/voice",
        data=consent,
        headers=_signed_headers("http://localhost/twilio/voice", consent),
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "<Stream" in body
    assert "wss://vot.example.test/twilio/media" in body
    assert "no_raw_audio" in body


def test_twilio_session_status_returns_redacted_state(twilio_client):
    client, gateway = twilio_client
    session = gateway.store.create("CA123", {"From": "***23"})

    response = client.get(f"/api/v1/twilio/sessions/{session['session_id']}")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["session_id"] == session["session_id"]
    assert payload["raw_audio_retained"] is False


def test_twilio_media_event_replay_decodes_frame(twilio_client):
    client, gateway = twilio_client
    session = gateway.store.create("CA123", {})
    event = {
        "event": "media",
        "media": {
            "payload": base64.b64encode(b"\xff" * 160).decode("ascii"),
        },
    }

    response = client.post(
        f"/twilio/media/events?session_id={session['session_id']}",
        json=event,
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["accepted"] is True

    updated = gateway.store.get(session["session_id"])
    assert updated["frames_received"] == 1
    assert updated["raw_audio_retained"] is False
