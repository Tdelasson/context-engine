# ADR-016: Canonical HTTP API, core application facade and React frontend

- **Status:** Proposed
- **Date:** 2026-11-12
- **Related issues:** #87, #88, #89, #90, #91, #92, #93

## Context

The only interface to Context Engine is the Streamlit Agent Workbench. The current-state
design (`docs/product/current-state-design/`) describes a three-column application with a
thread of runs and a per-run technical inspector. Streamlit cannot reproduce that layout or
its visual style, and the design now needs a live view of a run and an interactive approval
prompt.

The architecture overview already plans an embedded Python API and a local HTTP + JSON API
under `/api/v1` that expose the same domain semantics through thin adapters (section 4). It
lists the HTTP framework as not yet locked. `context_engine.core` and `context_engine.api`
exist as empty packages.

Application composition (`build_live_workbench`) and the run/source facade
(`WorkbenchApplication`) are framework-independent, but they live in the `workbench` package
next to the Streamlit code. `workbench/presentation.py` converts runtime contracts into
display text.

The project has no JavaScript tooling. The core package has no runtime dependencies.

## Decision

### 1. Core application facade

Move settings, live composition, the document catalog and the facade from `workbench` into
`context_engine.core`. The facade is the domain API: prepare the corpus, start a run, read
runs, manage sources, recover the source index, and report configuration and dependency
status. It returns structured records, not display strings. It imports no web framework and
no Streamlit.

Runs are held in an in-memory registry owned by the application object. One run is active at
a time; starting a second fails with an explicit typed error. Runs survive a page reload but
not a process restart. Each run executes on a worker thread and records its events (ADR-015).

### 2. HTTP API with FastAPI

`context_engine.api` is a thin FastAPI adapter over the facade, installed through an optional
`api` extra. It is the first slice of the canonical `/api/v1` API, not a private backend for
one screen.

| Resource | Endpoints |
| --- | --- |
| Runs | `POST /runs`, `GET /runs`, `GET /runs/{id}`, `GET /runs/{id}/events`, `POST /runs/{id}/approval` |
| Sources | `GET /sources`, `POST /sources`, `DELETE /sources/{id}`, `DELETE /sources`, `POST /sources/recover` |
| System | `GET /system` |

- Run responses carry typed domain data: outcome, status, iterations, tool traces, tool
  results with evidence and stage diagnostics, selection diagnostics, and configuration.
  Clients derive lifecycle and pipeline views themselves.
- `GET /runs/{id}/events` is a server-sent event stream. It replays recorded events in
  sequence order, continues live, and closes after the run-finished event.
- `POST /runs` answers `409` while a run is active.
- Request and response schemas are Pydantic models. The OpenAPI document is the contract from
  which the TypeScript client types are generated.
- The server binds to loopback by default. There is no authentication; the API is for local
  use and the documentation says so.
- Retrieval strategy, reranking and evidence selection remain application configuration and
  are read-only through the API.

FastAPI is chosen for typed schemas with validation, multipart uploads, streaming responses
and a generated OpenAPI document.

### 3. Interactive tool approval

An application setting lists tool names that require approval. It is empty by default, so
default behavior is unchanged. When set, the application composes a policy that returns
`REQUIRE_APPROVAL` for those tools and an approval resolver that blocks the run's worker
until `POST /runs/{id}/approval` supplies a decision. While waiting, the run has status
`awaiting_approval`.

An unanswered request resolves as rejected after a configurable timeout. Rejection and
timeout use the existing rejected path in the Tool Runtime and are reported as failures. The
model cannot influence which tools require approval or the timeout. Approval never bypasses
the Tool Runtime boundary (ADR-002).

### 4. React frontend

A React and TypeScript single-page application in a top-level `frontend/` directory, built
with Vite.

- **Styling:** plain CSS carried over from the mockups as design tokens plus per-component
  CSS modules. No component library or utility framework.
- **Routing:** a URL per screen and run, such as `/runs/:id` and `/knowledge`, with the open
  inspector reflected in the URL.
- **Data:** generated API types; the client renders what the API reports and holds no
  business logic. It never infers that a run succeeded.
- **Live view:** the client subscribes to a run's event stream and fills in the lifecycle,
  state timeline, timings and token usage as events arrive.
- **Tests:** Vitest and Testing Library for view-derivation logic and key components, with
  type-check and lint, against fake API data. No browser automation initially.
- **CI:** a Node job is added alongside the Python job.
- **Serving:** `npm run build` produces static files that the Python server serves on the
  same port as the API. In development the Vite server proxies API calls. Built files are not
  committed.

### 5. Streamlit

Streamlit stays unchanged until the React application reaches feature parity. It is then
removed, with its tests and dependency, in its own pull request (#93). Done: #93 removed the
workbench package, the `workbench` extra and the Streamlit dependency.

## Delivery order

1. #86 Runtime run events (ADR-015).
2. #87 Core application facade.
3. #88 HTTP API.
4. #89 Approval flow.
5. #90 Design update for running and awaiting-approval states.
6. #91 React scaffold and run thread with live inspector.
7. #92 Knowledge sources screen.
8. #93 Remove Streamlit.

## Alternatives considered

- **Keep Streamlit and restyle it.** No new stack, but it cannot deliver the layout, the
  per-run inspector or a live stream.
- **Server-rendered Python with HTMX.** Reuses the mockup markup, needs no Node toolchain and
  is testable with pytest. Rejected because the project wants the JSON API as a first-class
  interface and a conventional client for richer interaction later.
- **JSON API with hand-written JavaScript and no build step.** Avoids Node, but leaves the
  rendering logic without types or test tooling.
- **A workbench-only backend instead of the canonical API.** Smaller and quicker, but it would
  be a second API to retire when the canonical one arrives.
- **Wrap `WorkbenchApplication` in place.** Avoids moving code, but the canonical API would
  depend on a package that is being retired.
- **Starlette or the standard library.** Fewer dependencies, but schemas, validation and
  client types would be hand-written on both sides and could drift.
- **Blocking run request, or start-then-poll.** Both are simpler than a stream. Blocking
  shows nothing until the end and cannot support approval. Polling works but delivers steps
  late and needs the same recorded events anyway.
- **SQLite run persistence.** Enables history across restarts, but introduces the persistence
  architecture before M6 defines what a run record must hold.
- **Committing the built frontend.** Lets users skip Node, at the cost of generated files in
  git and a bundle that can go stale against its source.

## Consequences

- Node.js becomes a requirement for building and developing the UI, and CI gains a second
  toolchain. Contributors who only touch Python still need Node to run the complete UI.
- The project gains FastAPI, Pydantic and Uvicorn as optional dependencies. The core package
  keeps zero required dependencies.
- The canonical API's first resources are shaped by today's single-run, document-search
  application. M6 context work is expected to extend it; `/api/v1` versioning is the
  mitigation, and breaking changes before v1.0 are accepted.
- View derivation moves from tested Python (`presentation.py`) into the client, so the
  frontend tests carry that coverage.
- A loopback API without authentication is acceptable only for local use. Any other
  deployment needs a separate security decision.
- In-memory runs and a single active run are deliberate limits. Multiple server processes
  against one collection remain unsupported (ADR-009).
- A waiting approval occupies the single run slot until answered or timed out.
- The current-state mockups must be extended (#90) before the run view is built, because
  they state that there is no live view.
- Until #93 lands there are two UIs to keep working.
