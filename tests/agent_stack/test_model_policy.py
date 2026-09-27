import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "agent-stack" / "bin" / "agent_model_policy.py"
loader = SourceFileLoader("agent_model_policy_test", str(POLICY_PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
policy = importlib.util.module_from_spec(spec)
loader.exec_module(policy)


def fresh_usage():
    return {
        "fresh": True,
        "used_percent": 10,
        "ordinary_usage_allowed": True,
        "resets_at": 123,
    }


def test_premium_route_does_not_replace_hermes_parent(monkeypatch):
    monkeypatch.setattr(policy, "_usage_state", fresh_usage)
    decision = policy.decide(
        {
            "agent": "quantlab-hermes",
            "safety_profile": "quantlab",
            "preferred_model_tier": "sol",
            "attempts": 0,
        }
    )
    assert decision["tier"] == "sol"
    assert decision["selected_agent"] == "quantlab-hermes"
    assert decision["coordinator_agent"] == "quantlab-hermes"
    assert decision["executor_agent"] == "quantlab-sol"
    assert decision["model"] == "gpt-6-sol"
    assert decision["routing_scope"] == "child_node"


def test_retry_count_changes_executor_not_parent(monkeypatch):
    monkeypatch.setattr(policy, "_usage_state", fresh_usage)
    decision = policy.decide(
        {
            "agent": "quantlab-hermes",
            "safety_profile": "quantlab",
            "attempts": 3,
            "complexity_score": 0.9,
        }
    )

    assert decision["selected_agent"] == "quantlab-hermes"
    assert decision["executor_agent"] == "quantlab-astra"
    assert decision["tier"] == "astra"


def test_custom_coordinator_remains_stable(monkeypatch):
    monkeypatch.setattr(policy, "_usage_state", fresh_usage)
    decision = policy.decide(
        {
            "agent": "quantlab-sol",
            "coordinator_agent": "quantlab-hermes",
            "safety_profile": "quantlab",
            "preferred_model_tier": "astra",
            "attempts": 0,
        }
    )

    assert decision["selected_agent"] == "quantlab-hermes"
    assert decision["coordinator_agent"] == "quantlab-hermes"
    assert decision["executor_agent"] == "quantlab-astra"
