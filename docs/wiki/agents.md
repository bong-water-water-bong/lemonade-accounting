# Agent Guidelines & Safe Zones

This document provides specialized guidance for AI agents (and human developers) on safe operating procedures, boundaries, and tasks that are strictly out-of-scope in `lemonade-accounting`.

## Agent Safe Zones (Allowed Territory)

Agents are encouraged to modify, optimize, or extend the following modules:

- **`src/lemonade_accounting/ingest.py`**: Optimizing parsing performance, handling hybrid format schema variations, or tweaking wall-clock timeout checks.
- **`src/lemonade_accounting/closer.py`**: Modifying daily close summaries or calculating metrics from cashier events.
- **`src/lemonade_accounting/csv_export.py`**: Adding or refining CSV columns generated for accountants, provided they derive solely from standard `CashierEvent` inputs.
- **`src/lemonade_accounting/cli.py`**: Extending CLI argument parsing or error handling messages.
- **Tests**: Adding pytest test cases, mock event logs, or edge-case validation checks under the `tests/` directory.

Any code change is considered safe only if:
1. `make test` runs and passes successfully.
2. `make lint` and `make type` report zero errors.
3. It strictly respects the **Hard Rules** listed below.

---

## Out-of-Scope / Unsafe Zones (Do NOT Touch)

The following areas are strictly forbidden for autonomous changes. Modifying these without human verification or explicit instruction will result in PR rejection:

### 1. Payment Integrations
- **No wallets, gateways, card readers, or processor integrations** (e.g. Stripe, PayPal, Square).
- Accounting only processes daily closures and reconciles cash; it does not authorize, verify, or move actual funds.

### 2. Modifying Cashier State
- **Accounting must remain strictly read-only.**
- Do not add APIs, write commands, or append logic targeting `lemonade-cashier` event logs or cashier databases.

### 3. Customer Data & PII
- **Do not collect, store, or process Customer PII** (Personally Identifiable Information).
- Customer names, phone numbers, loyalty details, credit card numbers, audio recordings, or photos must never be persisted, logged, or exported.

### 4. Cloud Services / Integrations
- **No external network connections or cloud pushes.**
- All processing must be offline and run locally. Do not write integrations to push reports to cloud accounting services (e.g., QuickBooks Online, Xero) or automatic tax filing systems.

### 5. Runtime Third-Party Dependencies
- **No new third-party packages in `dependencies`** within `pyproject.toml`.
- The runtime code must remain standard-library-only, with the sole exception of the `lemonade-store` package.

---

## Agent Workflow Rules

- **Pre-Change and Post-Change Summaries**: Always write a plain-English explanation of your intent before making edits, and a summary of completed actions afterward.
- **Incremental Steps**: Break down complex features into small, testable commits. Do not attempt multiple large structural edits simultaneously.
- **Error Handling**: Do not let standard exceptions leak from parsing code. Translate bad JSON, format mismatches, and timeouts into `IngestError` instances inside `ingest.py`.

## Related Docs
- [README.md](file:///home/bcloud/multica_workspaces/eb279b7e-f49c-4099-a687-c1af978f0a5d/5e8bc9a5/workdir/lemonade-accounting/docs/wiki/README.md) — Mission and entry point
- [architecture.md](file:///home/bcloud/multica_workspaces/eb279b7e-f49c-4099-a687-c1af978f0a5d/5e8bc9a5/workdir/lemonade-accounting/docs/wiki/architecture.md) — Pipeline and ingestion architecture
- [conventions.md](file:///home/bcloud/multica_workspaces/eb279b7e-f49c-4099-a687-c1af978f0a5d/5e8bc9a5/workdir/lemonade-accounting/docs/wiki/conventions.md) — Standards and style guides
- [runbook.md](file:///home/bcloud/multica_workspaces/eb279b7e-f49c-4099-a687-c1af978f0a5d/5e8bc9a5/workdir/lemonade-accounting/docs/wiki/runbook.md) — Execution and validation runbook
