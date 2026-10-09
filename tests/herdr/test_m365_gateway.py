from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from herdr.m365_gateway import (
    AzureCliTokenProvider,
    ErrorCode,
    GatewayConfig,
    GatewayError,
    HttpResponse,
    M365Gateway,
    Source,
)


URL = (
    "https://example.environment.api.powerplatform.com/"
    "powerautomate/automations/direct/workflows/abc/triggers/manual/paths/invoke?api-version=1"
)
TENANT = "00000000-0000-0000-0000-000000000001"


def config(tmp_path: Path, **overrides) -> GatewayConfig:
    azure = tmp_path / ".azure"
    azure.mkdir(mode=0o700)
    values = dict(
        endpoint_url=URL,
        tenant_id=TENANT,
        azure_config_dir=str(azure),
        timeout_seconds=30.0,
        poll_timeout_seconds=20.0,
        poll_interval_seconds=1.0,
        max_attempts=3,
    )
    values.update(overrides)
    return GatewayConfig(**values)


def token() -> str:
    return "a" * 300 + "." + "b" * 300 + "." + "c" * 300


def ok(answer="ok", conversation_id="cid") -> HttpResponse:
    return HttpResponse(
        200, {"Content-Type": "application/json"},
        json.dumps({"answer": answer, "conversation_id": conversation_id}).encode(),
    )


def test_config_requires_https_powerplatform_host_and_closed_env(tmp_path):
    env = {
        "HERDR_M365_GATEWAY_URL": URL,
        "HERDR_M365_TENANT_ID": TENANT,
        "HERDR_M365_AZURE_CONFIG_DIR": str(tmp_path / ".azure"),
    }
    (tmp_path / ".azure").mkdir(mode=0o700)
    item = GatewayConfig.from_env(env)
    assert item.endpoint_url == URL
    with pytest.raises(GatewayError) as denied:
        GatewayConfig(
            endpoint_url="https://attacker.example/api",
            tenant_id=TENANT,
            azure_config_dir=str(tmp_path / ".azure"),
        )
    assert denied.value.code is ErrorCode.GATEWAY_UNAVAILABLE


def test_token_provider_uses_dedicated_cache_without_exposing_token(tmp_path):
    cfg = config(tmp_path)
    seen = {}

    def runner(args, **kwargs):
        seen["args"] = list(args)
        seen["env"] = dict(kwargs["env"])
        return SimpleNamespace(returncode=0, stdout=token() + "\n", stderr="")

    provider = AzureCliTokenProvider(cfg, runner=runner)
    assert provider() == token()
    assert seen["args"][:3] == ["az", "account", "get-access-token"]
    assert seen["env"]["AZURE_CONFIG_DIR"] == cfg.azure_config_dir


def test_token_provider_maps_interactive_login_to_auth_required(tmp_path):
    cfg = config(tmp_path)

    def runner(*_args, **_kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="Please run az login")

    with pytest.raises(GatewayError) as denied:
        AzureCliTokenProvider(cfg, runner=runner)()
    assert denied.value.code is ErrorCode.AUTH_REQUIRED
    assert not denied.value.retryable


def test_gateway_single_source_contract_and_prompt_scope(tmp_path):
    cfg = config(tmp_path)
    seen = []

    def transport(method, url, headers, body, timeout):
        seen.append((method, url, headers, json.loads(body), timeout))
        return ok("mail-result", "mail-cid")

    gateway = M365Gateway(cfg, token_provider=token, transport=transport)
    result = gateway.query("Qimarox", sources=(Source.OUTLOOK,), request_id="req-1")
    assert result.status == "completed"
    assert not result.partial
    assert result.sources[0].answer == "mail-result"
    assert result.sources[0].conversation_id == "mail-cid"
    payload = seen[0][3]
    assert payload.keys() == {"query"}
    assert "Outlook" in payload["query"]
    assert "veřejný web" in payload["query"]
    assert "Qimarox" in payload["query"]


def test_multi_source_fanout_keeps_provenance_and_partial_results(tmp_path):
    cfg = config(tmp_path, max_attempts=1)

    def transport(_method, _url, _headers, body, _timeout):
        prompt = json.loads(body)["query"]
        if "Teams" in prompt:
            return HttpResponse(503, {}, b"")
        if "SharePoint" in prompt:
            return ok("sharepoint", "sp-cid")
        return ok("outlook", "mail-cid")

    gateway = M365Gateway(cfg, token_provider=token, transport=transport)
    result = gateway.query(
        "Qimarox",
        sources=(Source.OUTLOOK, Source.TEAMS, Source.SHAREPOINT),
        request_id="req-2",
    )
    assert result.status == "completed"
    assert result.partial
    by_source = {item.source: item for item in result.sources}
    assert by_source[Source.OUTLOOK].status == "ok"
    assert by_source[Source.SHAREPOINT].status == "ok"
    assert by_source[Source.TEAMS].status == "error"
    assert by_source[Source.TEAMS].error_code is ErrorCode.UPSTREAM_TRANSIENT
    assert "[OUTLOOK]" in result.answer and "[SHAREPOINT]" in result.answer


def test_transient_500_retries_but_auth_does_not(tmp_path):
    cfg = config(tmp_path, max_attempts=3)
    calls = []
    sleeps = []

    def transport(_method, _url, _headers, _body, _timeout):
        calls.append(1)
        return HttpResponse(500, {}, b"") if len(calls) == 1 else ok("recovered")

    gateway = M365Gateway(cfg, token_provider=token, transport=transport, sleep=sleeps.append)
    result = gateway.query("x", sources=(Source.OUTLOOK,))
    assert result.sources[0].answer == "recovered"
    assert len(calls) == 2
    assert sleeps == [1]

    auth_calls = []
    def forbidden(*_args):
        auth_calls.append(1)
        return HttpResponse(403, {}, b"")

    gateway = M365Gateway(cfg, token_provider=token, transport=forbidden, sleep=sleeps.append)
    result = gateway.query("x", sources=(Source.OUTLOOK,))
    assert result.status == "error"
    assert result.sources[0].error_code is ErrorCode.AUTH_FORBIDDEN
    assert len(auth_calls) == 1


def test_system_error_answer_is_transient_and_retried(tmp_path):
    cfg = config(tmp_path, max_attempts=2)
    calls = []

    def transport(*_args):
        calls.append(1)
        if len(calls) == 1:
            return ok("Kód chyby: SystemError. ID konverzace: hidden")
        return ok("good")

    result = M365Gateway(
        cfg, token_provider=token, transport=transport, sleep=lambda _x: None
    ).query("x", sources=(Source.OUTLOOK,))
    assert result.sources[0].answer == "good"
    assert len(calls) == 2


def test_async_202_polls_location(tmp_path):
    cfg = config(tmp_path)
    location = (
        "https://poll.environment.api.powerplatform.com/"
        "powerautomate/operations/123"
    )
    calls = []
    clock = {"value": 0.0}

    def now():
        return clock["value"]

    def transport(method, url, headers, body, _timeout):
        calls.append((method, url, headers, body))
        if method == "POST":
            return HttpResponse(202, {"Location": location}, b"")
        clock["value"] = 0.1
        return ok("async-result", "async-cid")

    result = M365Gateway(
        cfg, token_provider=token, transport=transport, sleep=lambda _x: None, now=now
    ).query("x", sources=(Source.SHAREPOINT,))
    assert result.sources[0].answer == "async-result"
    assert [item[0] for item in calls] == ["POST", "GET"]
    assert calls[1][1] == location
    assert calls[1][3] is None


def test_untrusted_async_location_is_denied(tmp_path):
    cfg = config(tmp_path, max_attempts=1)
    def transport(*_args):
        return HttpResponse(202, {"Location": "https://attacker.example/result"}, b"")
    result = M365Gateway(cfg, token_provider=token, transport=transport).query(
        "x", sources=(Source.OUTLOOK,))
    assert result.status == "error"
    assert result.sources[0].error_code is ErrorCode.GATEWAY_UNAVAILABLE


def test_conversation_id_only_allowed_for_single_source(tmp_path):
    gateway = M365Gateway(config(tmp_path), token_provider=token, transport=lambda *_: ok())
    with pytest.raises(GatewayError) as denied:
        gateway.query(
            "x",
            sources=(Source.OUTLOOK, Source.TEAMS),
            conversation_id="existing",
        )
    assert denied.value.code is ErrorCode.INVALID_REQUEST

    seen = {}
    def transport(_method, _url, _headers, body, _timeout):
        seen.update(json.loads(body))
        return ok()
    gateway = M365Gateway(config(tmp_path), token_provider=token, transport=transport)
    gateway.query("x", sources=(Source.TEAMS,), conversation_id="existing")
    assert seen["conversation_id"] == "existing"


def test_health_checks_only_identity_not_mail_content(tmp_path):
    calls = []
    gateway = M365Gateway(
        config(tmp_path),
        token_provider=lambda: calls.append("token") or token(),
        transport=lambda *_args: (_ for _ in ()).throw(AssertionError("network must not run")),
    )
    assert gateway.health() == {"status": "ready"}
    assert calls == ["token"]


def test_query_is_bounded_and_source_enum_is_closed(tmp_path):
    gateway = M365Gateway(config(tmp_path), token_provider=token, transport=lambda *_: ok())
    with pytest.raises(GatewayError) as denied:
        gateway.query("x" * 20000, sources=(Source.OUTLOOK,))
    assert denied.value.code is ErrorCode.INVALID_REQUEST
    with pytest.raises(GatewayError):
        gateway.query("x", sources=("web",))
