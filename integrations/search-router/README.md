# Search Router — Perplexity cost-aware wiring

Adding PERPLEXITY_API_KEY does not make Perplexity the default.

- FAST: keyless first; Perplexity Fast only after free search fails.
- Quality-sensitive DEEP: Perplexity standard search first, then keyless full-page extraction.
- Other DEEP: keyless first.
- BROWSER: local browser.

Optional limits:
- SEARCH_ROUTER_PERPLEXITY_DAILY_CAP_USD (default 1.00, shared atomically across Maják and QuantLab)
- SEARCH_ROUTER_PERPLEXITY_FAST_COST_USD (default 0.001)
- SEARCH_ROUTER_PERPLEXITY_WEB_COST_USD (default 0.005)

Do not set web.backend to perplexity. The Search Router owns paid-provider selection and budget enforcement.
