# Context Engine frontend

React and TypeScript single-page app for the Context Engine HTTP API
(see [ADR-016](../docs/architecture/decisions/ADR-016-http-api-and-react-frontend.md) and the
[design mockups](../docs/product/current-state-design/README.md)).

```bash
npm ci
npm run dev        # http://localhost:5173, proxies /api to http://127.0.0.1:8000
npm run check      # typecheck, lint, test, build
```

- `src/api/` — fetch client, SSE subscription, and `schema.d.ts` generated from the API's
  OpenAPI document (`npm run gen:api`; regenerate after any API schema change).
- `src/derive/` — pure view derivation from structured data: lifecycle, state timeline,
  timings, token usage, retrieval pipeline. The client renders what the API reports and never
  infers success.
- `src/state/` — run list, system description, and the live run hook (snapshot plus events).
- `src/components/`, `src/pages/` — UI, styled with plain CSS: tokens in `src/styles/tokens.css`
  and a CSS module per component.

Tests use Vitest and Testing Library against fake API data; they need no server, model or
Qdrant. Runs are never persisted in the browser: a reload restores them from the API.
