# Context Engine — AI Development Instructions

## Project

Context Engine is a local-first runtime for
context-aware, deterministic AI agents.

The project is primarily a learning and engineering
project focused on:

- Agentic AI
- Deterministic tool use
- Modern RAG
- Vector search
- Embeddings
- MLOps
- Local LLM inference
- AI observability

## Core Principles

1. Prefer deterministic execution over autonomous execution.
2. LLMs propose actions; tools execute actions.
3. All tool inputs must be schema validated.
4. Business logic must not live inside prompts.
5. Components must be independently testable.
6. Prefer local inference where practical.
7. Keep provider-specific code behind abstractions.
8. Avoid unnecessary dependencies.

## Development Rules

- Do not modify architecture without documenting the decision.
- Add tests for new functionality.
- Run tests before committing.
- Do not introduce dependencies without justification.
- Keep modules small and composable.
- Update documentation when architecture changes.

## Git Rules

- Use feature branches.
- Never commit directly to main.
- Use conventional commit messages.
- Every meaningful feature should have a pull request.

## AI Agent Rules

Before modifying code:

1. Read relevant documentation.
2. Inspect existing implementation.
3. Identify affected modules.
4. Propose an implementation plan.

After modifying code:

1. Run relevant tests.
2. Run linting/type checks.
3. Review the diff.
4. Update documentation if necessary.

Never make broad architectural changes without approval.