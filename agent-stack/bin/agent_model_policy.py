"""Cost/limit-aware model tier policy for Agent Platform tasks."""
import json
import os
import time
from pathlib import Path

POLICY_VERSION = "cost-aware-v1.1-hermes-parent"
SOFT_LIMIT_PCT = 70
HARD_LIMIT_PCT = 90
USAGE_PATH = Path("/var/lib/agent-platform-herdr/codex-usage.json")
TELEMETRY_PATH = Path("/var/lib/agent-platform-herdr/model-routing.json")

FREE_AGENT = "quantlab-hermes"
SOL_AGENT = "quantlab-sol"
ASTRA_AGENT = "quantlab-astra"

PROVIDER_FAILURE_MARKERS = (
    "usage limit",
    "rate limit",
    "http 429",
    "too many requests",
    "provider unavailable",
)

COMPLEXITY_MARKERS = (
    "architecture",
    "cross-repo",
    "concurrency",
    "dependency",
    "dynamic child",
    "fencing",
    "recovery",
    "security",
    "migration",
    "admission control",
    "review blocker",
)

def _bounded_score(value, default=0.45):
    try:
        score = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, score))

def _usage_state():
    try:
        raw = json.loads(USAGE_PATH.read_text(encoding="utf-8"))
        observed = int(raw["observed_at"])
        rate = raw["rate_limit"]

        used = int(rate["used_percent"])
        ordinary = bool(rate["ordinary_usage_allowed"])
        fresh = 0 <= int(time.time()) - observed <= 900
        if not (0 <= used <= 100):
            raise ValueError("used_percent")
        return {
            "fresh": fresh,
            "used_percent": used,
            "ordinary_usage_allowed": ordinary,
            "resets_at": rate.get("resets_at"),
        }
    except Exception:
        return {
            "fresh": False,
            "used_percent": None,
            "ordinary_usage_allowed": False,
            "resets_at": None,
        }

def _complexity(task):
    explicit = task.get("complexity_score")
    if explicit is not None:
        return _bounded_score(explicit)
    text = str(task.get("prompt") or "").lower()
    score = 0.45

    score += min(0.30, sum(0.04 for marker in COMPLEXITY_MARKERS if marker in text))
    if len(text) > 8000:
        score += 0.08
    issue = task.get("issue")
    if isinstance(issue, int) and 229 <= issue <= 237:
        score += 0.08
    risk = str(task.get("risk_class") or "").lower()
    if risk == "high":
        score += 0.10
    elif risk == "critical":
        score += 0.18
    return round(min(1.0, score), 3)

def _provider_failure(task):
    error = str(task.get("last_error") or "").lower()
    return any(marker in error for marker in PROVIDER_FAILURE_MARKERS)

def decide(task):
    requested = str(task.get("agent") or FREE_AGENT)
    profile = str(task.get("safety_profile") or "quantlab")
    coordinator = str(
        task.get("coordinator_agent")
        or (FREE_AGENT if profile == "quantlab" else requested)
    )
    attempt = int(task.get("attempts") or 0)
    complexity = _complexity(task)
    usage = _usage_state()

    if profile != "quantlab":
        return {
            "policy_version": POLICY_VERSION,
            "tier": "profile-default",
            "selected_agent": requested,
            "model": "profile-router",
            "reason": "non_quantlab_profile",
            "attempt": attempt,
            "complexity_score": complexity,
            "codex_used_percent": usage["used_percent"],
            "codex_resets_at": usage["resets_at"],
            "soft_limit_pct": SOFT_LIMIT_PCT,
            "hard_limit_pct": HARD_LIMIT_PCT,
            "astra_escalation": False,
        }

    preferred = str(task.get("preferred_model_tier") or "").lower()
    if preferred == "free":
        tier, reason = "free", "explicit_free_request"
    elif requested == ASTRA_AGENT or preferred == "astra":
        tier, reason = "astra", "explicit_astra_request"
    elif requested in {SOL_AGENT, "quantlab-codex"} or preferred == "sol":
        tier, reason = "sol", "explicit_sol_request"
    elif _provider_failure(task) and attempt >= 1:
        tier, reason = "sol", "free_provider_failed"
    elif attempt >= 3 and complexity >= 0.78:
        tier, reason = "astra", "cheap_and_sol_attempts_exhausted"
    elif attempt >= 2:
        tier, reason = "sol", "cheap_attempts_exhausted"
    elif complexity >= 0.75:
        tier, reason = "sol", "high_complexity_capability_floor"
    else:
        tier, reason = "free", "cheapest_capable_first"

    used = usage["used_percent"]
    if tier in {"sol", "astra"} and (not usage["fresh"] or not usage["ordinary_usage_allowed"]):
        tier, reason = "free", "premium_budget_state_unavailable"
    elif tier in {"sol", "astra"} and used is not None and used >= HARD_LIMIT_PCT:
        tier, reason = "free", "hard_limit_reserve"
    elif tier == "astra" and used is not None and used >= SOFT_LIMIT_PCT:
        if attempt >= 2:
            tier, reason = "sol", "soft_limit_astra_reserved"
        else:
            tier, reason = "free", "soft_limit_astra_reserved"
    elif tier == "sol" and used is not None and used >= SOFT_LIMIT_PCT and attempt < 3:
        tier, reason = "free", "soft_limit_premium_conservation"

    executor_agent = {"free": FREE_AGENT, "sol": SOL_AGENT, "astra": ASTRA_AGENT}[tier]
    executor_model = {
        "free": "nous-adaptive-free",
        "sol": "gpt-6-sol",
        "astra": "gpt-6-astra",
    }[tier]
    return {
        "policy_version": POLICY_VERSION,
        "tier": tier,
        "selected_agent": coordinator,
        "coordinator_agent": coordinator,
        "executor_agent": executor_agent,
        "model": executor_model,
        "routing_scope": "child_node",
        "reason": reason,
        "attempt": attempt,
        "complexity_score": complexity,
        "codex_used_percent": used,
        "codex_resets_at": usage["resets_at"],
        "soft_limit_pct": SOFT_LIMIT_PCT,
        "hard_limit_pct": HARD_LIMIT_PCT,
        "astra_escalation": tier == "astra",
    }

def record(task, decision):
    if decision.get("tier") == "profile-default":
        return
    now = int(time.time())
    empty = {
        "version": 1,
        "observed_at": now,
        "policy": {
            "version": POLICY_VERSION,
            "soft_limit_pct": SOFT_LIMIT_PCT,
            "hard_limit_pct": HARD_LIMIT_PCT,
        },
        "totals": {
            "decisions": 0,
            "free": 0,
            "sol": 0,
            "astra": 0,
            "astra_escalations": 0,
            "premium_denied": 0,
        },
        "recent": [],
    }
    try:
        state = json.loads(TELEMETRY_PATH.read_text(encoding="utf-8"))
        if state.get("version") != 1:
            state = empty
    except Exception:
        state = empty

    tier = decision["tier"]
    totals = state["totals"]
    totals["decisions"] = int(totals.get("decisions", 0)) + 1
    if tier in {"free", "sol", "astra"}:
        totals[tier] = int(totals.get(tier, 0)) + 1
    if decision.get("astra_escalation"):
        totals["astra_escalations"] = int(totals.get("astra_escalations", 0)) + 1
    reason = str(decision.get("reason") or "")
    if "limit" in reason or "budget_state" in reason:
        totals["premium_denied"] = int(totals.get("premium_denied", 0)) + 1

    row = {
        "at": now,
        "task_id": str(task.get("id") or "")[:128],
        "issue": task.get("issue") if isinstance(task.get("issue"), int) else None,
        "attempt": int(decision["attempt"]),
        "delivery_reconcile_count": int(task.get("delivery_reconcile_count") or 0),
        "tier": tier,
        "model": str(decision["model"]),
        "selected_agent": str(decision["selected_agent"]),
        "coordinator_agent": str(
            decision.get("coordinator_agent") or decision["selected_agent"]
        ),
        "executor_agent": str(
            decision.get("executor_agent") or decision["selected_agent"]
        ),
        "routing_scope": str(decision.get("routing_scope") or "root"),
        "reason": reason,
        "complexity_score": decision["complexity_score"],
        "codex_used_percent": decision["codex_used_percent"],
    }
    state["observed_at"] = now
    state["policy"] = empty["policy"]
    state["recent"] = (list(state.get("recent") or []) + [row])[-200:]
    tmp = TELEMETRY_PATH.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(state, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    os.chmod(tmp, 0o640)
    os.replace(tmp, TELEMETRY_PATH)
