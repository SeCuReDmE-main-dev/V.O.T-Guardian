# Twilio Media Streams Runbook

V.O.T Guardian uses Twilio Programmable Voice and Media Streams as a supervised
education and fraud-awareness review surface. The first implementation is
voice-only. SMS and WhatsApp messaging remain disabled until a separate
Twilio Verify or A2P 10DLC review is complete.

## Runtime Surfaces

| Surface | Purpose |
| --- | --- |
| `POST /twilio/voice` | Twilio inbound voice webhook. Validates Twilio signature and returns consent-first TwiML. |
| `WS /twilio/media` | Twilio Media Streams endpoint. Receives live audio events over `wss`. |
| `POST /twilio/media/events` | Local replay endpoint for synthetic Media Stream JSON fixtures. |
| `GET /api/v1/twilio/sessions/<session_id>` | Redacted frontend polling endpoint for live review state. |

## Environment

```powershell
$env:TWILIO_ACCOUNT_SID="AC..."
$env:TWILIO_AUTH_TOKEN="..."
$env:TWILIO_VOICE_NUMBER="+1..."
$env:TWILIO_PUBLIC_BASE_URL="https://your-public-host.example"
$env:TWILIO_MEDIA_WS_URL="wss://your-public-host.example/twilio/media"
$env:TWILIO_VALIDATE_SIGNATURES="true"
$env:TWILIO_DEMO_MODE="false"
```

Optional safeguards:

```powershell
$env:TWILIO_MAX_MEDIA_BUFFER_BYTES="256000"
$env:TWILIO_MAX_CALL_DURATION_SECONDS="300"
$env:TWILIO_ALLOWED_CALLERS="+15145550123,+15145550999"
```

## Local And Staging Checklist

1. Run the Flask API from `developpement` with the project virtual environment.
2. Expose the API through a public HTTPS tunnel or staging host.
3. Configure the Twilio voice number webhook to `POST /twilio/voice`.
4. Confirm the public webhook URL exactly matches what signature validation sees.
5. Use a real `wss://` Media Stream URL. Twilio Media Streams does not use plain `ws://`.
6. Place one test call from an approved test caller.
7. Press `1` only after the consent prompt.
8. Verify the frontend live panel shows frames, bytes, no raw audio retention, and a human-review state.
9. Check Twilio Debugger for webhook, TwiML, TLS, and stream errors.
10. Record only metadata: session id, timestamp, call SID, status, and debugger outcome.

## Safety Boundary

- Raw call audio is never written to disk by the Twilio gateway.
- Live media payloads are decoded into short in-memory frames, reviewed, then zeroed.
- Review labels are limited to `review required`, `signal quality concern`,
  `uncertain voice-risk indicator`, `evidence gap`, and `human review needed`.
- V.O.T Guardian must not claim production fraud detection, biometric identity,
  emergency response, law-enforcement authority, or compliance authority.
- Any result is a supervised classroom artifact until a qualified human review
  and a separate production readiness gate exist.

## Compliance Notes

- Voice-only Media Streams does not by itself require A2P 10DLC registration.
- Any future application-to-person SMS/MMS to US recipients through a 10DLC
  number requires the appropriate A2P 10DLC path.
- User verification by SMS should use Twilio Verify before building custom
  messaging flows.
- Keep opt-in, opt-out, help, and consent copy documented before enabling SMS.

## Failure And Rollback

| Failure | Action |
| --- | --- |
| Invalid Twilio signature | Confirm `TWILIO_AUTH_TOKEN`, public host, proxy headers, scheme, and exact webhook URL. |
| No WebSocket connection | Confirm `TWILIO_MEDIA_WS_URL` starts with `wss://` and the host supports WebSocket upgrade. |
| Buffer limit exceeded | Treat as `evidence gap`, purge buffers, shorten call window, and inspect stream rate. |
| Twilio Debugger error | Save error code and timestamp, disable the webhook if user-facing calls are affected. |
| Privacy concern | Disable Twilio number webhook, preserve metadata only, and run a safety review. |

## Manual Acceptance

- Signed inbound webhook returns consent TwiML.
- Pressing `1` returns TwiML with `<Start><Stream>`.
- Media frames create review artifacts without storing raw audio.
- `GET /api/v1/twilio/sessions/<session_id>` returns redacted state.
- Frontend panel shows `raw_audio_retained: false`.
- Twilio Debugger is clean for the test call.
