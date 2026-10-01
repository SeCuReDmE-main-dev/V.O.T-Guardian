# Optional local observability

Datadog SDKs, agent and provider credentials have been removed. Technical OTLP
metrics use the standard library and are disabled by default. Enable them only
with an owned collector on literal `127.0.0.1:4318` or `[::1]:4318`.
The optional Compose collector uses the `observability` profile, a loopback host
port and a local `debug` exporter. It has no Docker socket or cloud exporter.
An existing listener on that port must be identified before enabling delivery.
The collector in another container is not reachable through the API container's
loopback; container deployment needs a separately reviewed network contract.

Only fixed counters and technical durations are exported. Voice features,
prediction, confidence, call/session identifiers and hashes are excluded.
Transport failures do not bypass authentication or interrupt product responses.

Tenebris audit entries use a separate local logger with bounded redacted metadata.
The API retains its PostgreSQL audit persistence. Neither a logger nor software
tests certify immutable storage, deletion timing or legal compliance. The current
Tenebris sandbox destruction method is a simulation; validate real E2B destruction
before making a production guarantee. No sandbox is created by telemetry setup.
