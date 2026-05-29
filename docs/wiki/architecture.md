# Architecture

> Daily close, cash reconciliation, and CSV export. Reads cashier JSONL events (including native logs and store.event.v1 envelopes), projects them to standard representation, and emits `accounting.*` envelope events.

## Overview
`lemonade-accounting` is a read-only consumer of cashier event logs. It projects financial summaries without modifying the append-only source log.

```
                  [cashier JSONL log]
                           │
                           ▼
                  lemonade_accounting
                      (ingest.py)
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
       (closer.py)                (csv_export.py)
             │                           │
             ▼                           ▼
[accounting.daily_close]        [CSV Exports]
```

## Ingestion Pipeline (`ingest.py`)
The `ingest.py` module is the single source of knowledge for cashier event shapes. It accepts cashier events in two formats:

1. **Native Cashier JSONL**: A flat JSON object containing audit fields at the top level:
   - `seq`: The transaction sequence number (int)
   - `ts`: ISO-8601 UTC timestamp (str)
   - `type`: Cashier event type (str)
   - `payload`: Event-specific data (dict)
   - `prev`: SHA-256 hash of the previous record (str)
   - `hash`: SHA-256 hash of the current record (str)

2. **Store Envelope Events (`store.event.v1`)**: Hybrid/envelope events containing a `schema_version = "store.event.v1"` field.
   - Loaded and validated using `lemonade_store.events.load_event`.
   - Events are filtered to process only those belonging to the `cashier` department.
   - These envelopes are projected back to a uniform `CashierEvent` object by mapping envelope payload properties to native cashier fields:
     - `payload.original_seq` ➔ `seq`
     - `payload.original_prev` ➔ `prev`
     - `payload.original_hash` ➔ `hash`
     - Timestamp, type, and payload are retrieved from the envelope event.

## Key Modules
- [ingest.py](../../src/lemonade_accounting/ingest.py) — Parses, validates, and standardizes cashier events from files with a configurable wall-clock timeout guard.
- [closer.py](../../src/lemonade_accounting/closer.py) — Enforces daily close business logic, accumulates transactions, and builds the signed/hashed `accounting.daily_close` store envelope.
- [csv_export.py](../../src/lemonade_accounting/csv_export.py) — Translates cashier events to a standardized tabular CSV format for use by traditional accounting software.
- [cli.py](../../src/lemonade_accounting/cli.py) — Implements the `lemonade-accounting close` command line interface.

## Invariants
- **Read-Only**: The accounting system must never write to cashier log streams or databases.
- **Precision**: Floats are prohibited for currency. All monetary operations must employ python's `Decimal` type.
- **Determinism**: Daily close outputs (including the generated `event_id`) must be byte-for-byte identical when re-run with the same input events, date, and store identifier.
- **No Third-Party Runtime Dependencies**: With the exception of `lemonade-store` (shared event models), the core library utilizes python's standard library only.
- **Time Limits**: File operations must check wall-clock budgets periodically to prevent blocking.

## Related Docs
- [README.md](README.md) — Mission and entry point
- [conventions.md](conventions.md) — Coding styles & patterns
- [runbook.md](runbook.md) — Executing CLI commands & test suites
- [agents.md](agents.md) — Rules, limits, and safe change zones
