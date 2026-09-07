from src.webmcp import DOMAIN_TOOLS, TOOLS, invoke, manifest


def test_catalogue_has_ten_domain_and_two_common_tools() -> None:
    assert manifest()["schema"] == "securedme.webmcp.v1"
    assert len(DOMAIN_TOOLS) == 10
    assert len(TOOLS) == len({tool.name for tool in TOOLS}) == 12
    assert all(tool["inputSchema"]["additionalProperties"] is False for tool in manifest()["tools"])
    assert all(set(tool["inputSchema"]["required"]) <= set(tool["inputSchema"]["properties"]) for tool in manifest()["tools"])


def test_model_readiness_never_accepts_random_weights() -> None:
    response = invoke("vot_inspect_model_readiness")
    assert response["ok"] is True
    assert response["result"]["randomWeightsAllowed"] is False
    assert response["result"]["fallbackClassificationAllowed"] is False


def test_audio_capability_fails_closed_without_admitted_runtime() -> None:
    response = invoke("vot_extract_voice_review_features", {"assetRef": "asset:fixture", "approvalId": "a", "idempotencyKey": "i"})
    assert response["ok"] is False
    assert response["error"]["code"] == "RUNTIME_NOT_CONFIGURED"


def test_review_stays_undetermined_and_staged() -> None:
    response = invoke("vot_stage_voice_risk_review", {"featureReceiptRef": "receipt:fixture"})
    assert response["result"]["classification"] == "UNDETERMINED"
    assert response["result"]["durableWrite"] is False


def test_unknown_tool_fails_closed() -> None:
    assert invoke("vot_impersonate_voice")["error"]["code"] == "TOOL_NOT_ALLOWED"
