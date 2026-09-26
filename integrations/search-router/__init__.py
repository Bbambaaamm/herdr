from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from hermes_constants import get_hermes_home

FAST = "fast"
DEEP = "deep"
BROWSER = "browser"
_URL_RE = re.compile(r"https?://[^\s<>()\[\]{}\"']+", re.I)

_BROWSER_TERMS = (
    "click", "login", "sign in", "form", "dashboard", "javascript", "js-heavy",
    "interactive", "interact", "screenshot", "open page", "current page",
    "klik", "přihl", "formulář", "dashboard", "interaktiv", "screenshot",
    "otevři strán", "na stránce", "web app", "webová aplikace",
)
_DEEP_TERMS = (
    "research", "deep", "compare", "comparison", "verify", "cross-check",
    "multiple sources", "official sources", "evidence", "investigate", "report",
    "legislation", "regulation", "law", "grant", "funding", "tender",
    "academic", "paper", "study", "rešerš", "podrob", "porovnej", "ověř",
    "zdroje", "oficiální", "důkazy", "legislativ", "zákon", "vyhlášk",
    "dotac", "výzv", "tendr", "studie", "výzkum", "všechny možnosti",
)

_PPLX_QUALITY_TERMS = (
    "verify", "cross-check", "official sources", "evidence", "legislation",
    "regulation", "law", "grant", "funding", "tender", "academic", "paper",
    "study", "filing", "regulatory", "earnings", "ověř", "oficiální",
    "důkazy", "legislativ", "zákon", "vyhlášk", "regulac", "nařízení",
    "dotac", "výzv", "tendr", "studie", "výzkum", "výroční zpráva",
)
_PPLX_FAST_COST_USD = 0.001
_PPLX_WEB_COST_USD = 0.005
_PPLX_DAILY_CAP_USD = 1.0

def _home() -> Path:
    return Path(get_hermes_home())

def _profile() -> str:
    home = _home()
    return home.name if home.parent.name == "profiles" else "default"

def _state_dir() -> Path:
    target = _home() / "search-router"
    target.mkdir(parents=True, exist_ok=True)
    return target

def _db() -> sqlite3.Connection:
    con = sqlite3.connect(_state_dir() / "search.db", timeout=5)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_call_id TEXT, session_id TEXT, task_id TEXT,
            query_hash TEXT NOT NULL, query_chars INTEGER NOT NULL,
            route_mode TEXT NOT NULL, route_reason TEXT NOT NULL,
            requested_provider TEXT, actual_provider TEXT,
            fallback_provider TEXT, fallback_used INTEGER DEFAULT 0,
            started_at REAL NOT NULL, ended_at REAL, duration_ms INTEGER,
            result_count INTEGER DEFAULT 0, extract_count INTEGER DEFAULT 0,
            success INTEGER, cost_usd REAL, error_type TEXT
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_search_started ON searches(started_at)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_search_route ON searches(route_mode, actual_provider)")
    con.commit()
    return con

def _budget_db() -> sqlite3.Connection:
    home = _home()
    root = home.parent.parent if home.parent.name == "profiles" else home
    root.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(root / "search-router-budget.db", timeout=15, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""
        CREATE TABLE IF NOT EXISTS paid_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reserved_at REAL NOT NULL,
            provider TEXT NOT NULL,
            cost_usd REAL NOT NULL,
            query_hash TEXT NOT NULL
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_paid_usage_reserved ON paid_usage(reserved_at)")
    return con

def _hash_query(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8", "ignore")).hexdigest()[:16]

def _urls(query: str) -> list[str]:
    return [value.rstrip(".,;:)") for value in _URL_RE.findall(query or "")][:5]

def _classify(query: str, limit: int) -> tuple[str, str]:
    text = (query or "").lower()
    browser_hits = [term for term in _BROWSER_TERMS if term in text]
    deep_hits = [term for term in _DEEP_TERMS if term in text]
    urls = _urls(query)
    if browser_hits:
        return BROWSER, "dynamic/interactive intent: " + ", ".join(browser_hits[:3])
    if urls:
        return DEEP, "explicit URL requires page retrieval"
    if len(deep_hits) >= 1 or int(limit or 5) >= 8:
        reason = ", ".join(deep_hits[:3]) if deep_hits else "requested result breadth"
        return DEEP, "multi-source/deep intent: " + reason
    return FAST, "low-latency factual lookup"

def _parse(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return {"success": False, "error": "unsupported result"}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {"success": False, "error": "invalid result"}
    except Exception:
        return {"success": False, "error": raw[:500] or "empty result"}

def _hits(data: dict[str, Any]) -> list[dict[str, Any]]:
    web = (data.get("data") or {}).get("web") if isinstance(data.get("data"), dict) else None
    return [row for row in web if isinstance(row, dict)] if isinstance(web, list) else []
def _is_ok(data: dict[str, Any]) -> bool:
    if data.get("success") is False or data.get("error"):
        return False
    return bool(_hits(data)) or data.get("success") is True

def _requested_provider() -> str:
    try:
        from tools.tool_backend_helpers import read_selection, selection_exists
        selected = read_selection("web")
        if selected == "nous":
            return "nous-managed"
    except Exception:
        selected = None
        selection_exists = lambda _section: False
    try:
        from tools.web_tools import _get_search_backend
        backend = str(_get_search_backend() or "unknown")
        if selected is None and not selection_exists("web"):
            try:
                from agent.web_search_registry import get_provider
                provider = get_provider(backend)
                if provider is not None and not provider.is_available() and provider.is_keyless_available():
                    return _safe_provider(backend + "-keyless")
            except Exception:
                pass
        return backend
    except Exception:
        return "unknown"

def _safe_provider(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_./:-]+", "_", value or "unknown")
    return value[:128] or "unknown"

def _join_provider(*parts: str) -> str:
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        clean = _safe_provider(part)
        if clean and clean not in out:
            out.append(clean)
    return _safe_provider("_".join(out))
def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default

def _perplexity_available() -> bool:
    try:
        from agent.web_search_provider import get_provider_env
        return bool(get_provider_env("PERPLEXITY_API_KEY"))
    except Exception:
        return False

def _perplexity_daily_cap() -> float:
    return max(0.0, _env_float("SEARCH_ROUTER_PERPLEXITY_DAILY_CAP_USD", _PPLX_DAILY_CAP_USD))

def _perplexity_cost(fast: bool) -> float:
    name = "SEARCH_ROUTER_PERPLEXITY_FAST_COST_USD" if fast else "SEARCH_ROUTER_PERPLEXITY_WEB_COST_USD"
    default = _PPLX_FAST_COST_USD if fast else _PPLX_WEB_COST_USD
    return max(0.0, _env_float(name, default))

def _paid_spend_today() -> float:
    day_start = (int(time.time()) // 86400) * 86400
    con = _budget_db()
    try:
        row = con.execute(
            "SELECT COALESCE(SUM(cost_usd),0) FROM paid_usage WHERE reserved_at >= ?",
            (day_start,),
        ).fetchone()
        return float(row[0] or 0.0)
    finally:
        con.close()

def _reserve_paid(cost: float, provider: str, query: str) -> int | None:
    cost = max(0.0, float(cost))
    cap = _perplexity_daily_cap()
    if cap <= 0 or cost <= 0:
        return None
    now = time.time()
    day_start = (int(now) // 86400) * 86400
    con = _budget_db()
    try:
        con.execute("BEGIN IMMEDIATE")
        spent = float(con.execute(
            "SELECT COALESCE(SUM(cost_usd),0) FROM paid_usage WHERE reserved_at >= ?",
            (day_start,),
        ).fetchone()[0] or 0.0)
        if spent + cost > cap + 1e-12:
            con.rollback()
            return None
        cur = con.execute(
            "INSERT INTO paid_usage(reserved_at,provider,cost_usd,query_hash) VALUES(?,?,?,?)",
            (now, _safe_provider(provider), cost, _hash_query(query)),
        )
        con.commit()
        return int(cur.lastrowid)
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def _quality_requires_perplexity(query: str) -> bool:
    text = (query or "").lower()
    return any(term in text for term in _PPLX_QUALITY_TERMS)

def _external_cost(provider: str) -> float | None:
    parts = [part for part in (provider or "").split("_") if part]
    if not parts:
        return None
    total = 0.0
    paid_seen = False
    unknown_seen = False
    for part in parts:
        if part == "perplexity-fast":
            total += _perplexity_cost(True)
            paid_seen = True
        elif part in ("perplexity-web", "perplexity"):
            total += _perplexity_cost(False)
            paid_seen = True
        elif part.endswith("-keyless") or part in ("local-browser", "keyless-rescue"):
            continue
        else:
            unknown_seen = True
    if paid_seen:
        return total
    if not unknown_seen:
        return 0.0
    if "nous-managed" in provider:
        return None
    return None

async def _perplexity_search(query: str, limit: int, *, fast: bool) -> tuple[dict[str, Any], str]:
    try:
        from plugins.web.perplexity.provider import _normalize_search_results, _perplexity_request
        payload = {
            "query": query,
            "max_results": max(1, min(int(limit or 5), 20)),
            "search_context_size": "low",
            "search_type": "fast" if fast else "web",
        }
        raw = await asyncio.to_thread(_perplexity_request, "search", payload)
        return _normalize_search_results(raw), ("perplexity-fast" if fast else "perplexity-web")
    except Exception as exc:
        return {"success": False, "error": f"Perplexity search failed: {type(exc).__name__}: {str(exc)[:300]}"}, (
            "perplexity-fast" if fast else "perplexity-web"
        )

async def _primary_search(query: str, limit: int) -> tuple[dict[str, Any], str]:
    from tools.web_tools import web_search_tool
    raw = await asyncio.to_thread(web_search_tool, query, limit)
    data = _parse(raw)
    provider = _requested_provider()
    payload = data.get("data") if isinstance(data.get("data"), dict) else {}
    served = payload.get("served_by") if isinstance(payload, dict) else None
    if isinstance(served, str) and served:
        provider = _safe_provider(served + "-keyless")
    return data, provider

async def _keyless_search(query: str, limit: int) -> tuple[dict[str, Any], str]:
    from plugins.web.keyless_mcp import search_with_failover
    data = await asyncio.to_thread(search_with_failover, "parallel", query, limit)
    served = ((data.get("data") or {}).get("served_by")
              if isinstance(data.get("data"), dict) else None) or "parallel"
    return data, _safe_provider(str(served) + "-keyless")

async def _browser_navigate(url: str, task_id: str = "") -> tuple[bool, str]:
    from tools.browser_tool import browser_navigate
    raw = await asyncio.to_thread(browser_navigate, url, task_id or None)
    text = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)
    parsed = _parse(text)
    failed = bool(parsed.get("error")) if text.lstrip().startswith("{") else not bool(text.strip())
    return (not failed), text[:24000]

async def _search_with_fallback(
    query: str, limit: int, task_id: str = "", *, prefer_quality: bool = False
) -> tuple[dict[str, Any], str, bool, str | None]:
    if not _perplexity_available():
        primary, provider = await _primary_search(query, limit)
        payload = primary.get("data") if isinstance(primary.get("data"), dict) else {}
        if payload.get("rescued_from") and _is_ok(primary):
            served = str(payload.get("served_by") or "keyless")
            rescue_provider = _safe_provider(served + "-keyless")
            return primary, rescue_provider, True, rescue_provider
        if _is_ok(primary) and _hits(primary):
            return primary, provider, False, None
        fallback, fallback_provider = await _keyless_search(query, limit)
        if _is_ok(fallback) and _hits(fallback):
            return fallback, fallback_provider, True, fallback_provider
        url = "https://duckduckgo.com/?q=" + quote_plus(query)
        ok, snapshot = await _browser_navigate(url, task_id)
        if ok:
            return {
                "success": True,
                "data": {"web": [], "browser_snapshot": snapshot},
            }, "local-browser", True, "local-browser"
        if fallback.get("error"):
            primary.setdefault("fallback_error", str(fallback.get("error"))[:500])
        return primary, provider, True, fallback_provider

    if prefer_quality:
        cost = _perplexity_cost(False)
        reservation = _reserve_paid(cost, "perplexity-web", query)
        if reservation is not None:
            paid, paid_provider = await _perplexity_search(query, limit, fast=False)
            if _is_ok(paid) and _hits(paid):
                return paid, paid_provider, False, None

    free, free_provider = await _keyless_search(query, limit)
    if _is_ok(free) and _hits(free):
        return free, free_provider, bool(prefer_quality), (free_provider if prefer_quality else None)

    if not prefer_quality:
        cost = _perplexity_cost(True)
        reservation = _reserve_paid(cost, "perplexity-fast", query)
        if reservation is not None:
            paid, paid_provider = await _perplexity_search(query, limit, fast=True)
            if _is_ok(paid) and _hits(paid):
                return paid, paid_provider, True, paid_provider

    url = "https://duckduckgo.com/?q=" + quote_plus(query)
    ok, snapshot = await _browser_navigate(url, task_id)
    if ok:
        return {
            "success": True,
            "data": {"web": [], "browser_snapshot": snapshot},
        }, "local-browser", True, "local-browser"
    return free, free_provider, True, "local-browser"

def _unique_urls(query: str, data: dict[str, Any], maximum: int = 3) -> list[str]:
    values = _urls(query)
    for row in _hits(data):
        url = row.get("url")
        if isinstance(url, str) and url.startswith(("http://", "https://")):
            values.append(url)
    seen: set[str] = set()
    return [u for u in values if not (u in seen or seen.add(u))][:maximum]

async def _extract(urls: list[str]) -> tuple[list[dict[str, Any]], str, bool]:
    if not urls:
        return [], "", False
    if _perplexity_available():
        from plugins.web.keyless_mcp import extract_with_failover
        fallback = await asyncio.to_thread(extract_with_failover, "parallel", urls)
        useful = [r for r in fallback if isinstance(r, dict) and r.get("content") and not r.get("error")]
        return fallback, "parallel-keyless", bool(useful)

    from tools.web_tools import web_extract_tool
    raw = await web_extract_tool(urls, "markdown", char_limit=6000)
    parsed = _parse(raw)
    rows = parsed.get("results") if isinstance(parsed.get("results"), list) else []
    useful = [r for r in rows if isinstance(r, dict) and r.get("content") and not r.get("error")]
    rescued = any(
        isinstance(r, dict) and isinstance(r.get("metadata"), dict)
        and r["metadata"].get("rescued_from")
        for r in rows
    )
    if useful:
        return rows, ("keyless-rescue" if rescued else _requested_provider()), rescued
    from plugins.web.keyless_mcp import extract_with_failover
    fallback = await asyncio.to_thread(extract_with_failover, "parallel", urls)
    useful = [r for r in fallback if isinstance(r, dict) and r.get("content") and not r.get("error")]
    return fallback, "parallel-keyless", bool(useful)

def _decorate(
    data: dict[str, Any], mode: str, reason: str, provider: str,
    fallback_used: bool, fallback_provider: str | None,
    extracted: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    out = dict(data)
    payload = dict(out.get("data") or {}) if isinstance(out.get("data"), dict) else {}
    payload["_search_router"] = {
        "mode": mode, "reason": reason, "provider": provider,
        "fallback_used": bool(fallback_used),
        "fallback_provider": fallback_provider,
    }
    if extracted is not None:
        payload["extracted"] = extracted
    out["data"] = payload
    return out

def _record(
    *, query: str, mode: str, reason: str, requested: str, provider: str,
    fallback_provider: str | None, fallback_used: bool, started: float,
    success: bool, result_count: int, extract_count: int,
    tool_call_id: str = "", session_id: str = "", task_id: str = "",
    error_type: str | None = None,
) -> None:
    ended = time.time()
    cost = _external_cost(provider)
    with _db() as con:
        con.execute("""
            INSERT INTO searches (
                tool_call_id,session_id,task_id,query_hash,query_chars,
                route_mode,route_reason,requested_provider,actual_provider,
                fallback_provider,fallback_used,started_at,ended_at,duration_ms,
                result_count,extract_count,success,cost_usd,error_type
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            tool_call_id or None, session_id or None, task_id or None,
            _hash_query(query), len(query), mode, reason, requested,
            _safe_provider(provider), _safe_provider(fallback_provider) if fallback_provider else None,
            int(bool(fallback_used)), started, ended, round((ended - started) * 1000),
            max(0, int(result_count)), max(0, int(extract_count)), int(bool(success)),
            cost, error_type,
        ))
        con.commit()

async def _handle(
    args: dict[str, Any], task_id: str = "", session_id: str = "",
    tool_call_id: str = "", **_: Any
) -> str:
    query = str((args or {}).get("query") or "").strip()
    try:
        limit = min(max(int((args or {}).get("limit", 5)), 1), 20)
    except (TypeError, ValueError):
        limit = 5
    if not query:
        return json.dumps({"success": False, "error": "query is required"})
    started = time.time()
    mode, reason = _classify(query, limit)
    requested = _requested_provider()
    provider = requested
    fallback_provider: str | None = None
    fallback_used = False
    extract_count = 0
    try:
        if mode == BROWSER:
            urls = _urls(query)
            search_data: dict[str, Any] | None = None
            if urls:
                target = urls[0]
            else:
                search_data, search_provider, sf, sfp = await _search_with_fallback(
                    query, max(limit, 5), task_id
                )
                provider, fallback_used, fallback_provider = search_provider, sf, sfp
                found = _unique_urls(query, search_data, 1)
                target = found[0] if found else "https://duckduckgo.com/?q=" + quote_plus(query)
            ok, snapshot = await _browser_navigate(target, task_id)
            provider = _join_provider(provider if not urls else "", "local-browser")
            result = {
                "success": ok,
                "data": {"web": _hits(search_data or {}), "browser_snapshot": snapshot, "url": target},
            }
            if not ok:
                result["error"] = "browser navigation failed"
            result = _decorate(
                result, mode, reason, provider, fallback_used, fallback_provider
            )
        elif mode == DEEP:
            result, provider, fallback_used, fallback_provider = await _search_with_fallback(
                query, max(limit, 8), task_id,
                prefer_quality=_quality_requires_perplexity(query),
            )
            urls = _unique_urls(query, result, 3)
            extracted, extract_provider, extract_fallback = await _extract(urls)
            if extract_provider:
                provider = _join_provider(provider, extract_provider)
            if extract_fallback:
                fallback_used = True
                fallback_provider = _join_provider(
                    fallback_provider or "", extract_provider
                )
            extract_count = sum(
                1 for row in extracted
                if isinstance(row, dict) and row.get("content") and not row.get("error")
            )
            result = _decorate(
                result, mode, reason, provider, fallback_used,
                fallback_provider, extracted
            )
        else:
            result, provider, fallback_used, fallback_provider = await _search_with_fallback(
                query, limit, task_id
            )
            result = _decorate(
                result, mode, reason, provider, fallback_used, fallback_provider
            )
        success = _is_ok(result)
        result_count = len(_hits(result))
        if mode == BROWSER and (result.get("data") or {}).get("browser_snapshot"):
            result_count = max(result_count, 1)
        _record(
            query=query, mode=mode, reason=reason, requested=requested, provider=provider,
            fallback_provider=fallback_provider, fallback_used=fallback_used, started=started,
            success=success, result_count=result_count, extract_count=extract_count,
            tool_call_id=tool_call_id, session_id=session_id, task_id=task_id,
            error_type=None if success else "route_failed",
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        _record(
            query=query, mode=mode, reason=reason, requested=requested, provider=provider,
            fallback_provider=fallback_provider, fallback_used=fallback_used, started=started,
            success=False, result_count=0, extract_count=0,
            tool_call_id=tool_call_id, session_id=session_id, task_id=task_id,
            error_type=type(exc).__name__[:80],
        )
        return json.dumps(
            {
                "success": False,
                "error": f"search router failed: {type(exc).__name__}: {str(exc)[:300]}",
            },
            ensure_ascii=False,
        )

def _status_text() -> str:
    return "\n".join([
        f"Search router [{_profile()}]",
        f"requested provider: {_requested_provider()}",
        "routes: fast -> free ring; deep -> quality-gated Perplexity + full-page extract; browser -> local browser",
        f"perplexity: {'enabled as escalation' if _perplexity_available() else 'disabled (no API key)'}; daily cap=USD {_perplexity_daily_cap():.2f}",
        "fallback: free keyless ring -> paid fast escalation (when enabled) -> local browser",
        "telemetry: query text is not stored; only hash + length",
    ])

def _last_text() -> str:
    with _db() as con:
        row = con.execute("SELECT * FROM searches ORDER BY id DESC LIMIT 1").fetchone()
    if row is None:
        return f"Search router last [{_profile()}]: no completed searches yet."
    return "\n".join([
        f"Search router last [{_profile()}]",
        f"mode={row['route_mode']} provider={row['actual_provider'] or '?'}",
        f"success={'YES' if row['success'] else 'NO'} fallback={'YES' if row['fallback_used'] else 'NO'}",
        f"latency={int(row['duration_ms'] or 0)}ms results={int(row['result_count'] or 0)} extracts={int(row['extract_count'] or 0)}",
        f"query={row['query_hash']} ({row['query_chars']} chars)",
        f"reason={row['route_reason']}",
    ])

def _report_text() -> str:
    with _db() as con:
        rows = con.execute("""
            SELECT route_mode, actual_provider, COUNT(*) n, SUM(success) ok,
                   AVG(duration_ms) avg_ms, SUM(fallback_used) fallbacks,
                   SUM(result_count) results, SUM(extract_count) extracts
            FROM searches GROUP BY route_mode,actual_provider
            ORDER BY n DESC,route_mode,actual_provider LIMIT 30
        """).fetchall()
    lines = [
        f"Search router report [{_profile()}]",
        "mode | provider | searches | success | avg latency | fallbacks | results | extracts",
    ]
    for row in rows:
        n = int(row["n"] or 0)
        rate = (int(row["ok"] or 0) / n) if n else 0
        lines.append(
            f"{row['route_mode']} | {row['actual_provider']} | {n} | {rate:.0%} | "
            f"{float(row['avg_ms'] or 0):.0f}ms | {int(row['fallbacks'] or 0)} | "
            f"{int(row['results'] or 0)} | {int(row['extracts'] or 0)}"
        )
    return "\n".join(lines)

def _command(raw_args: str) -> str:
    command = (raw_args or "").strip().lower()
    if not command or command == "status":
        return _status_text()
    if command == "last":
        return _last_text()
    if command == "report":
        return _report_text()
    return "Usage: /searchrouter [status|last|report]"

def register(ctx) -> None:
    _db().close()
    schema = {
        "name": "web_search",
        "description": (
            "Search through the local Search Router. It automatically uses fast search for "
            "ordinary lookups, search+extract for deep multi-source research, and the local "
            "browser for dynamic/interactive pages. Query text is not persisted in telemetry."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Web search query."},
                "limit": {
                    "type": "integer", "description": "Maximum results.", "minimum": 1,
                    "maximum": 20, "default": 5,
                },
            },
            "required": ["query"],
        },
    }
    ctx.register_tool(
        "web_search", "web", schema, _handle, is_async=True,
        description=schema["description"], emoji="🔎", override=True,
    )
    ctx.register_command(
        "searchrouter", handler=_command,
        description="Show Search Router status, last route and aggregate telemetry.",
    )
