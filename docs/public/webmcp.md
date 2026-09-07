# V.O.T Guardian WebMCP surface

V.O.T Guardian exposes ten defensive review tools and two shared SecuredMe companion tools through `developpement/src/webmcp.py`. The catalogue is available even when the local audio or trained-model runtime is absent; affected operations then return `RUNTIME_NOT_CONFIGURED` rather than a plausible result.

The surface never performs impersonation, surveillance, bypass, live telephony by default, or autonomous accusation. Raw audio is not a companion payload. Voice-derived features are not persisted by the analysis route, and missing decoders, models, or checkpoints fail closed. Human consent and review remain mandatory.

The companion uses the V.O.T-specific Stitch design document for its specialist palette while keeping accessible SecuredMe fallbacks and the persistent Hero Book identity.
