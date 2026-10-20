from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from herdr.capability import DataClass
from herdr.external_knowledge import KnowledgeRequest
from herdr.external_knowledge_host import (
    ExternalKnowledgeHostError, HostExternalKnowledgePolicy,
)
from herdr.security import PolicyDenied, ProviderRoute
from tests.herdr.test_external_knowledge_egress import configured_grant

EXAMPLE = Path(__file__).resolve().parents[2] / "deploy/herdr/external-knowledge.example.json"


def load_example(monkeypatch, raw):
    # Replace only the root reader; run the actual closed policy/route parser.
    def dummy_root_reader(path):
        assert path == EXAMPLE
        return copy.deepcopy(raw)

    def no_socket(*_args, **_kwargs):
        raise AssertionError("configuration contract tests must not open sockets")

    monkeypatch.setattr("herdr.external_knowledge_host._read_regular_root_policy", dummy_root_reader)
    monkeypatch.setattr("herdr.external_knowledge_host.socket.socket", no_socket)
    return HostExternalKnowledgePolicy.from_file(EXAMPLE)


def matching_grant(tmp_path, raw):
    grant = configured_grant(tmp_path)
    route = ProviderRoute.from_dict(raw["provider_capabilities"][0])
    return replace(grant,
        identity=replace(grant.identity, consumer="github:Example/project"),
        scope=replace(grant.scope, providers=(route.provider,)),
        provider_routes=(route,))


def test_documented_v2_example_authorizes_matching_synthetic_grant(tmp_path, monkeypatch):
    raw = json.loads(EXAMPLE.read_text())
    assert raw["version"] == 2
    route = raw["provider_capabilities"][0]
    assert route["base_url"] == "https://knowledge.example.invalid/v1"
    assert route["credential_refs"] == []
    policy = load_example(monkeypatch, raw)
    policy.authorize(matching_grant(tmp_path, raw), "example-provider",
        KnowledgeRequest.create("synthetic confidential input", ("mail",), request_id="example"))


def test_documented_legacy_shape_cannot_authorize_delivery(tmp_path, monkeypatch):
    raw = json.loads(EXAMPLE.read_text())
    grant = matching_grant(tmp_path, raw)
    raw.pop("provider_capabilities")
    raw["version"] = 1
    policy = load_example(monkeypatch, raw)
    with pytest.raises(PolicyDenied, match="capabilities_unverified"):
        policy.authorize(grant, "example-provider",
            KnowledgeRequest.create("synthetic", ("mail",), request_id="legacy"))


@pytest.mark.parametrize("change", ["missing_facts", "unknown_training", "extra_fact"])
def test_documented_v2_rejects_incomplete_or_unknown_facts(monkeypatch, change):
    raw = json.loads(EXAMPLE.read_text())
    if change == "missing_facts":
        raw.pop("provider_capabilities")
    elif change == "unknown_training":
        raw["provider_capabilities"][0]["training"] = "unknown"
    else:
        raw["provider_capabilities"][0]["model_self_attested"] = True
    with pytest.raises(ExternalKnowledgeHostError, match="policy_invalid"):
        load_example(monkeypatch, raw)


def test_documented_example_does_not_declassify_query(tmp_path, monkeypatch):
    raw = json.loads(EXAMPLE.read_text())
    grant = matching_grant(tmp_path, raw)
    raw["provider_capabilities"][0]["data_classes"] = [DataClass.PUBLIC.value]
    policy = load_example(monkeypatch, raw)
    with pytest.raises(PolicyDenied, match="data_class_denied"):
        policy.authorize(grant, "example-provider",
            KnowledgeRequest.create("synthetic", ("mail",), request_id="sensitive"))
