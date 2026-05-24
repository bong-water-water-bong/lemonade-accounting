# Architecture

> Daily close, cash reconciliation, and CSV export. Reads cashier JSONL events, emits `accounting.*` envelope events.

## Overview
lemonade-accounting is a read-only consumer of `lemonade-cashier` event logs. It never writes to cashier state — it projects financial summaries from the append-only JSONL event log.

```
lemonade-cashier JSONL log
        ↓
lemonade_accounting.reader  (reads & validates store.event.v1 envelopes)
        ↓
lemonade_accounting.engine  (double-entry bookkeeping, cash reconciliation)
        ↓
accounting.daily_close.v1   (emitted to shared event envelope)
accounting.discrepancy.v1   (emitted when cash-out != expected)
        ↓
CSV export / reports
```

## Key Modules
- `src/lemonade_accounting/reader.py` — reads and validates cashier JSONL
- `src/lemonade_accounting/engine.py` — cash reconciliation, daily close logic
- `src/lemonade_accounting/export.py` — CSV and summary report generation
- `src/lemonade_accounting/events.py` — `accounting.*` event type definitions

## Invariants
- **Never write to cashier log**: accounting is read-only. If you find yourself calling cashier write APIs, that's wrong.
- **Decimal only**: all monetary calculations use `Decimal`, same as cashier core.
- **Idempotent close**: running daily close twice produces the same result.
- **No external dependencies in core**: stdlib-only in `engine.py` and `reader.py`.

## How to Test
```bash
make test       # full suite
make lint       # flake8 + black
make type       # mypy
```

Test fixtures use synthetic cashier JSONL logs in `tests/fixtures/`.

## Current Priorities
- Reconciliation engine: comparing physical cash count to calculated expected cash
- Discrepancy detection and `accounting.discrepancy.v1` event emission
- CSV export for accountant hand-off

## Related
- [[README]] — mission and agent handoff
- `lemonade-cashier` — source of truth event log
- `lemonade-store` — umbrella event envelope definitions
