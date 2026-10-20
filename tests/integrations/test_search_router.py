import asyncio
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "integrations/search-router/__init__.py"
URLS = [
    "https://www.example.org/reference",
    "http://127.0.0.1/admin",
    "http://10.0.0.1/private",
    "http://169.254.169.254/latest/meta-data/",
    "http://224.0.0.1/",
    "http://0.0.0.0/",
    "http://[::1]/",
    "http://[fd00::1]/",
    "http://[fe80::1]/",
    "http://2130706433/",
    "http://0177.0.0.1/",
    "http://%31%32%37.0.0.1/",
    "https://public.example@127.0.0.1/",
    "https://public.example\\@127.0.0.1/",
    "https://rebind.example.test/changes-answer",
    "https://public.example.test/redirect-to-private",
]


@pytest.fixture
def router(monkeypatch, tmp_path):
    constants = types.ModuleType("hermes_constants")
    constants.get_hermes_home = lambda: tmp_path
    monkeypatch.setitem(sys.modules, "hermes_constants", constants)
    spec = importlib.util.spec_from_file_location("isolated_search_router", ROUTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "_record", lambda **kwargs: None)
    monkeypatch.setattr(module, "_requested_provider", lambda: "test-search")
    monkeypatch.setattr(module, "_perplexity_available", lambda: False)
    return module


@pytest.fixture
def url_sinks(monkeypatch):
    # Synthetic connectors have the vulnerable APIs, without network/DNS access.
    # A redirect or rebinding-capable connector cannot be made safe by a prior
    # hostname lookup. Until its transport can enforce policy, never call it.
    calls = []
    browser = types.ModuleType("tools.browser_tool")
    web = types.ModuleType("tools.web_tools")
    keyless = types.ModuleType("plugins.web.keyless_mcp")

    def navigate(url, task_id=None):
        calls.append(("browser", url))
        return "synthetic page"

    async def extract(urls, format, char_limit):
        calls.append(("web-extract", list(urls)))
        return json.dumps({"results": [{"url": u, "content": "synthetic"} for u in urls]})

    def fallback(provider, urls):
        calls.append(("keyless-extract", list(urls)))
        return [{"url": u, "content": "synthetic"} for u in urls]

    browser.browser_navigate = navigate
    web.web_extract_tool = extract
    keyless.extract_with_failover = fallback
    for name in ("tools", "plugins", "plugins.web"):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    for name, module in (
        ("tools.browser_tool", browser),
        ("tools.web_tools", web),
        ("plugins.web.keyless_mcp", keyless),
    ):
        monkeypatch.setitem(sys.modules, name, module)
    return calls


@pytest.mark.parametrize("url", URLS)
def test_navigation_never_delegates_uncontrolled_url(router, url_sinks, url):
    ok, snapshot = asyncio.run(router._browser_navigate(url, "task"))
    assert url_sinks == []
    assert ok is False
    assert snapshot == ""


@pytest.mark.parametrize("paid_available", [False, True])
def test_extraction_disables_every_connector_and_reports_each_url(
    router, url_sinks, monkeypatch, paid_available
):
    monkeypatch.setattr(router, "_perplexity_available", lambda: paid_available)
    rows, provider, fallback = asyncio.run(router._extract(URLS))
    assert url_sinks == []
    assert provider == ""
    assert fallback is False
    assert [row["url"] for row in rows] == URLS
    assert all(row["error_code"] == "unsafe_url_route_disabled" for row in rows)
    assert not any(row.get("content") for row in rows)


def test_empty_extraction_needs_no_connector(router, url_sinks):
    assert asyncio.run(router._extract([])) == ([], "", False)
    assert url_sinks == []


@pytest.mark.parametrize("paid_available,prefer_quality", [(False, False), (True, False), (True, True)])
def test_failed_search_has_no_browser_fallback(
    router, url_sinks, monkeypatch, paid_available, prefer_quality
):
    async def unavailable(query, limit):
        return {"success": False, "error": "synthetic unavailable"}, "test-search"

    monkeypatch.setattr(router, "_primary_search", unavailable)
    monkeypatch.setattr(router, "_keyless_search", unavailable)
    monkeypatch.setattr(router, "_perplexity_available", lambda: paid_available)
    monkeypatch.setattr(router, "_reserve_paid", lambda *args: None)
    data, provider, used, fallback = asyncio.run(
        router._search_with_fallback("normal query", 5, prefer_quality=prefer_quality)
    )
    assert url_sinks == []
    assert data["success"] is False
    assert provider == "test-search"
    assert fallback != "local-browser"


def test_explicit_browser_route_fails_without_search_or_navigation(router, url_sinks, monkeypatch):
    async def forbidden(*args, **kwargs):
        pytest.fail("disabled navigation must not fall through into another request")

    monkeypatch.setattr(router, "_search_with_fallback", forbidden)
    result = json.loads(asyncio.run(router._handle({"query": "open page http://127.0.0.1/admin"})))
    assert result["success"] is False
    assert result["error_code"] == "unsafe_url_route_disabled"
    assert url_sinks == []


def test_deep_search_keeps_results_without_following_hostile_hits(router, url_sinks, monkeypatch):
    async def search(query, limit, task_id="", **kwargs):
        return {"success": True, "data": {"web": [
            {"url": URLS[1], "title": "untrusted private result"},
            {"url": URLS[-1], "title": "untrusted redirect result"},
        ]}}, "test-search", False, None

    monkeypatch.setattr(router, "_search_with_fallback", search)
    result = json.loads(asyncio.run(router._handle({"query": "deep research", "limit": 8})))
    assert result["success"] is True
    assert len(result["data"]["web"]) == 2
    assert len(result["data"]["extracted"]) == 2
    assert all(row["error_code"] == "unsafe_url_route_disabled" for row in result["data"]["extracted"])
    assert url_sinks == []


def test_public_https_search_results_still_work(router, url_sinks, monkeypatch):
    calls = []
    async def search(query, limit):
        calls.append((query, limit))
        return {"success": True, "data": {"web": [
            {"url": URLS[0], "title": "Public reference"}
        ]}}, "test-search"

    async def forbidden(*args, **kwargs):
        pytest.fail("valid primary search must not require fallback")

    monkeypatch.setattr(router, "_primary_search", search)
    monkeypatch.setattr(router, "_keyless_search", forbidden)
    result = json.loads(asyncio.run(router._handle({"query": "ordinary factual lookup", "limit": 3})))
    assert result["success"] is True
    assert result["data"]["web"][0]["url"] == URLS[0]
    assert calls == [("ordinary factual lookup", 3)]
    assert url_sinks == []


def test_public_search_fallback_still_works(router, url_sinks, monkeypatch):
    async def primary(query, limit):
        return {"success": False, "error": "synthetic unavailable"}, "primary"

    async def fallback(query, limit):
        return {"success": True, "data": {"web": [{"url": URLS[0]}]}}, "keyless"

    monkeypatch.setattr(router, "_primary_search", primary)
    monkeypatch.setattr(router, "_keyless_search", fallback)
    data, provider, used, fallback_provider = asyncio.run(router._search_with_fallback("ordinary lookup", 3))
    assert data["success"] is True
    assert provider == fallback_provider == "keyless"
    assert used is True
    assert url_sinks == []
