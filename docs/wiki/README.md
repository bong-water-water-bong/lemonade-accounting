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
    - `src/lemonade_accounting/core.py`: Logic for daily close and reconciliation.
    - `src/lemonade_accounting/io.py`: Cashier log reading and CSV export logic.
- **Current Priorities**:
    - Implementing `accounting.cash_reconciled` for drawer-to-expected matching.
    - Expanding the barter ledger (`accounting.barter_recorded`).

## Decisions & Gotchas
- **Strings for Money**: All currency values in events are strings to preserve `Decimal` precision. Never use floats.
- **No Cloud Dependency**: Accounting must run entirely on the local Strix Halo workstation. No external API calls allowed.
- **Deterministic IDs**: `event_id` is derived from `store_id`, `date`, and a hash of the payload. Changing the payload format will change all future event IDs for the same data.
- **Wall-clock Budget**: The closer is designed to be fast (sub-5s) to avoid blocking other system operations.
