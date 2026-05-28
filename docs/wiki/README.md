# Project Wiki: Lemonade Accounting

## Mission
Provide deterministic, offline-first daily closing and cash reconciliation for the Lemonade Store suite. It serves as the bridge between the high-frequency cashier event log and the low-frequency financial records required by human accountants.

## Architecture
- **Closer Agent**: A deterministic process that reads `lemonade-cashier` events and emits `accounting.daily_close` envelopes.
- **Read-Only Core**: Accounting never modifies the source cashier logs; it only consumes and summarizes them.
- **Idempotency**: Given the same store ID and date, the closer produces byte-for-byte identical output (including event IDs) using SHA-256 hashing.
- **Shared Contracts**: Uses the `store.event.v1` envelope from `lemonade-store` for all emitted events.
- **CSV Bridge**: Generates human-readable CSV exports for traditional accounting tools, maintaining the "offline-capable" mandate.

## Agent Handoff
- **How to Test**:
    - `make test`: Runs the pytest suite.
    - `make lint`: Runs ruff for linting and formatting checks.
    - `make type`: Runs mypy for strict type checking.
- **Hot Paths**:
    - [closer.py](file:///home/bcloud/multica_workspaces_desktop-localhost-18088/eb279b7e-f49c-4099-a687-c1af978f0a5d/295c11a5/workdir/lemonade-accounting/src/lemonade_accounting/closer.py): Logic for daily close.
    - [ingest.py](file:///home/bcloud/multica_workspaces_desktop-localhost-18088/eb279b7e-f49c-4099-a687-c1af978f0a5d/295c11a5/workdir/lemonade-accounting/src/lemonade_accounting/ingest.py): Cashier log reading and validation.
    - [csv_export.py](file:///home/bcloud/multica_workspaces_desktop-localhost-18088/eb279b7e-f49c-4099-a687-c1af978f0a5d/295c11a5/workdir/lemonade-accounting/src/lemonade_accounting/csv_export.py): CSV export logic.
- **Current Priorities**:
    - Implementing `accounting.cash_reconciled` for drawer-to-expected matching.
    - Expanding the barter ledger (`accounting.barter_recorded`).

## Decisions & Gotchas
- **Strings for Money**: All currency values in events are strings to preserve `Decimal` precision. Never use floats.
- **No Cloud Dependency**: Accounting must run entirely on the local Strix Halo workstation. No external API calls allowed.
- **Deterministic IDs**: `event_id` is derived from `store_id`, `date`, and a hash of the payload. Changing the payload format will change all future event IDs for the same data.
- **Wall-clock Budget**: The closer is designed to be fast (sub-5s) to avoid blocking other system operations.

## OpenSpec Workflow

Use `openspec/` as the working standard for department changes:

- `openspec/project.md` defines this repo's department workflow.
- `openspec/specs/accounting/spec.md` records the active contract for this department.
- `openspec/changes/<change-id>/` holds proposal, design, and task files for active work.
- GitHub issues and PRs must name affected event types and approval gates.

Keep this repo aligned with `lemonade-store` when event contracts, owner approval gates, or department boundaries change.

## LLM Wiki Standard

This repo treats Andrej Karpathy's LLM Wiki pattern as the governing source for agent knowledge management: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

For this project, that means:

- `docs/wiki/` is the maintained project memory for architecture, decisions, gotchas, and onboarding.
- `AGENTS.md` is the agent instruction schema.
- `openspec/` is the structured change/spec layer.
- Raw source material stays in docs, examples, tests, issue/PR discussions, and committed specs.
- Agents must update the wiki when they learn durable repo knowledge that future agents need.

Keep wiki entries concise, factual, and linked back to concrete files, specs, or test evidence.

## Wiki Pages

- [architecture.md](file:///home/bcloud/multica_workspaces_desktop-localhost-18088/eb279b7e-f49c-4099-a687-c1af978f0a5d/295c11a5/workdir/lemonade-accounting/docs/wiki/architecture.md) — High-level accounting architecture and closer agent event ingestion pipeline.
- [conventions.md](file:///home/bcloud/multica_workspaces_desktop-localhost-18088/eb279b7e-f49c-4099-a687-c1af978f0a5d/295c11a5/workdir/lemonade-accounting/docs/wiki/conventions.md) — PEP 8, mypy strict typings, standard library core rules, and Decimal pricing math.
- [runbook.md](file:///home/bcloud/multica_workspaces_desktop-localhost-18088/eb279b7e-f49c-4099-a687-c1af978f0a5d/295c11a5/workdir/lemonade-accounting/docs/wiki/runbook.md) — Command lines, test suites, close procedures.
- [agents.md](file:///home/bcloud/multica_workspaces_desktop-localhost-18088/eb279b7e-f49c-4099-a687-c1af978f0a5d/295c11a5/workdir/lemonade-accounting/docs/wiki/agents.md) — Safety rules, actor roles, safe zones.

