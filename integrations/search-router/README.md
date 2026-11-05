# Search Router — Perplexity cost-aware wiring

Adding PERPLEXITY_API_KEY does not make Perplexity the default.

- FAST: keyless first; Perplexity Fast only after free search fails.
- Quality-sensitive DEEP: Perplexity standard search first, then keyless search.
- Other DEEP: keyless first. Search results remain available; full-page extraction is disabled.
- BROWSER: unavailable. Failed search does not fall back to browser navigation.

The installed browser and extraction connectors do not expose a trusted policy
at the actual connection boundary for destination addresses and redirect chains.
The router therefore never delegates URLs to those connectors, including
public-looking URLs that could redirect or change DNS answers. A separate DNS
precheck would not make that handoff safe. Enabling these routes requires a
connector that enforces this policy for every connection; no runtime switch
enables the unsafe route.

Optional limits:
- SEARCH_ROUTER_PERPLEXITY_DAILY_CAP_USD (default 1.00, shared atomically across Maják and QuantLab)
- SEARCH_ROUTER_PERPLEXITY_FAST_COST_USD (default 0.001)
- SEARCH_ROUTER_PERPLEXITY_WEB_COST_USD (default 0.005)

Do not set web.backend to perplexity. The Search Router owns paid-provider selection and budget enforcement.
