# Context Engine — AI Agent Instructions

## 1. Project Overview

Context Engine is a local-first AI platform for building context-aware, agentic applications.

The project is primarily an engineering and learning project focused on:

* Agentic AI
* Deterministic tool use
* Structured outputs
* Modern RAG
* Vector search
* Embeddings
* Local LLM inference
* Inference optimization
* MLOps
* Evaluation and observability

The first application built on top of Context Engine is a Context-Aware DJ that demonstrates the platform's capabilities through a real-world agentic application.

---

# 2. Core Engineering Principles

## 2.1 Deterministic execution

LLMs should propose actions, not directly execute them.

The preferred architecture is:

User intent
→ LLM reasoning
→ structured tool call
→ validation
→ policy check
→ deterministic tool execution
→ structured result
→ LLM

Never allow an LLM to directly perform side effects without passing through the appropriate tool and policy layer.

---

## 2.2 Explicit over implicit

Prefer explicit code, schemas, interfaces, and configuration over hidden behavior.

Avoid putting important business logic exclusively inside prompts.

Critical behavior must be represented in executable code wherever practical.

---

## 2.3 Type safety

Use strongly typed interfaces and structured data.

Tool inputs and outputs must use explicit schemas.

Invalid model output must be rejected rather than silently corrected when correctness or safety could be affected.

---

## 2.4 Testability

Components should be independently testable.

Prefer small, composable modules over large classes or functions with many responsibilities.

New functionality should include appropriate tests.

---

## 2.5 Provider independence

Do not tightly couple the application to a single LLM, embedding model, vector database, inference server, or external API unless there is a documented reason.

Use abstractions where provider independence provides meaningful value.

Do not create abstractions purely for the sake of abstraction.

---

## 2.6 Local-first

Context Engine should be capable of running locally wherever practical.

Prefer local inference and local data processing when doing so does not introduce disproportionate complexity.

Cloud services may be used for deployment, external integrations, monitoring, or functionality that cannot reasonably be performed locally.

---

## 2.7 Observability

Important AI operations should be observable.

Agent executions should make it possible to understand:

* what the agent attempted to do
* which tools were selected
* what arguments were generated
* which context was retrieved
* what actions were executed
* what errors occurred
* how long operations took

---

# 3. Repository Structure

The repository follows this general structure:

```text
context-engine/
│
├── AGENTS.md
├── README.md
│
├── docs/
│   ├── product/
│   ├── architecture/
│   ├── api/
│   ├── experiments/
│   └── learning/
│
├── src/
├── tests/
├── benchmarks/
├── scripts/
│
└── .github/
    ├── workflows/
    ├── ISSUE_TEMPLATE/
    └── pull_request_template.md
```

Before making architectural or significant implementation changes, inspect the relevant documentation under `docs/`.

---

# 4. Documentation Hierarchy

Use the following hierarchy:

### `README.md`

High-level project introduction, setup and quick start.

### `docs/product/`

Product requirements, roadmap, scope and user-facing requirements.

### `docs/architecture/`

System architecture, components, interfaces and architectural decisions.

### `docs/api/`

API contracts and external/internal API documentation.

### `docs/experiments/`

AI experiments, benchmarks, model comparisons and empirical results.

### `docs/learning/`

Technical notes and learning material created during development.

### `AGENTS.md`

Instructions and constraints for AI agents working on the repository.

Do not duplicate large sections of project documentation inside `AGENTS.md`.

---

# 5. Before Making Changes

Before modifying code:

1. Read this file.
2. Inspect the relevant existing code.
3. Read relevant architecture documentation.
4. Read the relevant GitHub issue or task.
5. Identify affected components.
6. Determine whether existing patterns should be reused.

For non-trivial changes, create or describe an implementation plan before making changes.

Do not begin by rewriting large parts of the codebase.

---

# 6. Implementation Rules

When implementing a feature:

1. Follow existing architectural patterns.
2. Keep changes focused on the requested task.
3. Avoid unrelated refactoring.
4. Prefer simple implementations over premature abstraction.
5. Add or update tests.
6. Update documentation when behavior or architecture changes.
7. Review the complete diff before considering the task complete.

Do not introduce new dependencies unless they provide clear value.

When introducing a dependency, consider:

* maintenance status
* license
* security
* project maturity
* performance
* whether the functionality can reasonably be implemented without it

---

# 7. AI / LLM Development Rules

LLM behavior must not be assumed to be deterministic unless explicitly configured and verified.

Use structured outputs when downstream code depends on model-generated data.

Validate model outputs before using them.

Prompts should not contain logic that belongs in application code.

Keep prompts versioned and reviewable when they are an important part of system behavior.

When changing an LLM, embedding model, reranker, retrieval strategy, or inference configuration:

* document the change
* benchmark where appropriate
* record relevant results
* consider whether evaluation results are affected

Do not optimize an AI component based solely on subjective output quality when measurable evaluation is possible.

---

# 8. Agent and Tool Rules

Tools are the controlled interface between agents and external systems.

Every tool should have:

* a unique name
* a clear description
* a typed input schema
* a typed output
* deterministic behavior where practical
* explicit error handling
* appropriate tests

Tools that cause external side effects should have an explicit permission or policy mechanism where appropriate.

Examples of side effects include:

* creating or deleting files
* modifying external data
* sending messages
* creating playlists
* making API mutations
* executing system commands

Never bypass the tool/policy layer simply because doing so is easier.

---

# 9. RAG and Retrieval Rules

Retrieval quality should be measured rather than assumed.

When modifying retrieval behavior, consider:

* chunking strategy
* embedding model
* metadata
* filtering
* dense retrieval
* sparse retrieval
* hybrid retrieval
* reranking
* context selection
* query transformation

Important retrieval changes should be evaluated using the project's benchmark datasets.

Do not judge a retrieval strategy solely by whether a few manually tested queries appear correct.

---

# 10. Model and Inference Rules

Model-related changes should consider:

* model quality
* latency
* memory usage
* VRAM usage
* throughput
* context length
* quantization
* hardware requirements

When comparing models or inference configurations, record measurable results where practical.

Do not optimize for maximum model size by default.

The goal is an effective local system, not simply the largest possible model.

---

# 11. Testing

At minimum, changes should include appropriate tests for:

* normal behavior
* invalid input
* expected failure modes
* important edge cases

AI-related functionality should use deterministic fixtures or controlled test cases wherever possible.

Do not make tests dependent on an external LLM or API unless the test is explicitly classified as an integration test.

Tests should be runnable locally.

Before opening a pull request, run the relevant test suite.

---

# 12. Git and Branching

Never commit directly to `main`.

Use feature branches.

Branch names should describe the change, for example:

```text
feature/tool-registry
feature/hybrid-retrieval
fix/tool-validation
experiment/embedding-model
```

Use clear commit messages.

Keep commits focused and logically meaningful.

Do not rewrite Git history or force-push shared branches unless explicitly requested.

---

# 13. Pull Requests

Every meaningful feature or fix should go through a pull request.

A pull request should explain:

* what changed
* why it changed
* how it was implemented
* how it was tested
* whether architecture or behavior changed
* whether documentation was updated

Keep pull requests focused.

Avoid combining unrelated changes into a single PR.

---

# 14. Architectural Changes

Do not make significant architectural changes silently.

Before changing:

* core interfaces
* data models
* agent execution flow
* retrieval architecture
* model abstraction
* persistence architecture
* security model
* deployment architecture

inspect the existing architecture documentation.

If the change is significant, document the decision in an Architecture Decision Record (ADR).

ADRs should explain:

* context
* decision
* alternatives considered
* consequences

---

# 15. Security and Secrets

Never commit:

* API keys
* access tokens
* passwords
* private credentials
* `.env` files containing secrets
* personal authentication data

Use environment variables or an appropriate secret-management mechanism.

Do not expose secrets in logs, tests, error messages, screenshots or documentation.

Treat external API access as an explicit capability.

---

# 16. Agent Autonomy

AI agents may make implementation decisions within the scope of their assigned task.

Agents must not independently:

* change project scope
* remove major functionality
* change core architecture
* introduce major infrastructure
* expose secrets
* disable security controls
* bypass tests
* bypass permission systems
* merge their own changes into `main`

When a task requires a decision outside its defined scope, stop and request clarification.

---

# 17. Completion Criteria

A task is not complete simply because the code works locally.

Before considering a task complete:

* [ ] Implementation is complete
* [ ] Tests are added or updated
* [ ] Relevant tests pass
* [ ] Linting/type checks pass where applicable
* [ ] The diff has been reviewed
* [ ] Documentation is updated if necessary
* [ ] No secrets or sensitive data were introduced
* [ ] The implementation follows the project's architecture

---

# 18. Working Style for AI Agents

Be concise and explicit.

Before significant changes, explain the intended approach.

Do not claim that something works without testing it.

Do not hide failures.

If an assumption is uncertain, state the assumption.

If the existing architecture conflicts with the requested implementation, explain the conflict instead of silently introducing a second architecture.

Prefer incremental changes that can be reviewed and reverted.

The goal is not to write the most code.

The goal is to make the smallest correct change that moves the project forward.
