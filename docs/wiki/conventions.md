# Coding Conventions

This document outlines the standard coding styles, naming practices, and design patterns enforced in `lemonade-accounting`.

## Monetary Values & Precision

- **Never use `float` for currency**: Binary floating-point representation causes rounding errors that violate financial integrity.
- **Always use `Decimal`**: Use Python's `decimal.Decimal` class for all calculations and accumulations in core modules.
- **Strings in JSON**: When serializing currency values to JSON envelopes or output files, format them as strings with two decimal places (e.g. `"1.50"`) to preserve decimal precision across different consuming platforms.

## Dependency Management

- **Runtime Constraints**: To maintain a lightweight, offline-capable service, the core package remains standard-library-only.
- **Allowed Extensions**: The only external runtime dependency is `lemonade-store`, which provides contract validation for the shared store envelopes. No third-party network clients, database connectors, or web servers may be added.

## Strict Type Safety

- **Full Typing**: All files must contain PEP 484/PEP 585 type annotations.
- **Strict Checks**: The project runs under `mypy --strict`. All code modifications must resolve type errors and ensure that no implicit optional or untyped signatures exist.

## Code Style & Formatting

- **Linter & Formatter**: We use [Ruff](https://github.com/astral-sh/ruff) for fast python linting and code formatting.
- **Line Length**: Max line length is set to `100` characters (configured in `pyproject.toml`).
- **Enforcement**: Run `make lint` to verify conformance and `make fmt` to automatically format files.

## Error Handling Pattern

- **Uniform Ingestion Errors**: The parser in `ingest.py` must catch all malformed inputs, schema validation errors, and timeout conditions, and wrap them in a single `IngestError`.
- **No Quiet Failures**: When reading from log streams, fail explicitly rather than silently dropping records or retrying indefinitely.

## Git & PR Workflow

- **Conventional Commits**: Commit messages must adhere to the Conventional Commits structure (e.g., `feat: ...`, `fix: ...`, `docs: ...`).
- **Test-Driven Changes**: Any functional change or bugfix must be accompanied by new pytest coverage. Ensure the build remains fully green.

## Related Docs
- [README.md](file:///home/bcloud/multica_workspaces/eb279b7e-f49c-4099-a687-c1af978f0a5d/5e8bc9a5/workdir/lemonade-accounting/docs/wiki/README.md) — Mission and entry point
- [architecture.md](file:///home/bcloud/multica_workspaces/eb279b7e-f49c-4099-a687-c1af978f0a5d/5e8bc9a5/workdir/lemonade-accounting/docs/wiki/architecture.md) — System design and data flows
- [runbook.md](file:///home/bcloud/multica_workspaces/eb279b7e-f49c-4099-a687-c1af978f0a5d/5e8bc9a5/workdir/lemonade-accounting/docs/wiki/runbook.md) — How to test and run the project
- [agents.md](file:///home/bcloud/multica_workspaces/eb279b7e-f49c-4099-a687-c1af978f0a5d/5e8bc9a5/workdir/lemonade-accounting/docs/wiki/agents.md) — Rules, limits, and safe change zones
