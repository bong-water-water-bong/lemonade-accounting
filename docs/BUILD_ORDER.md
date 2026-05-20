# Build order

This pins the frontier. A PR that adds a layer beyond the current
frontier should be rejected unless the frontier is reliably green.

## v0.1 — closer + daily_close + CSV (this repo, today)

- [x] `ingest.py`: read cashier `events.jsonl`.
- [x] `closer.py`: deterministic `accounting.daily_close`.
- [x] `csv_export.py`: per-transaction CSV.
- [x] `cli.py`: `lemonade-accounting close ...`.
- [x] Cashier-grade hygiene.

## v0.2 — cash drawer reconciliation

- Read cashier till open/close events (`cit.till.open`,
  `cit.till.close`).
- Compare expected vs counted; emit `accounting.cash_reconciled` with
  the diff and reason categories.

## v0.3 — barter ledger

- Read cashier barter events (`cashier.barter.recorded` when cashier
  starts emitting them in envelope shape, or the cashier-native form
  if earlier).
- Emit `accounting.barter_recorded` with attendant, value, and item
  references.

## v0.4 — expense and supplier-cost intake

- Consume `supplier.order.received` envelope events.
- Emit `accounting.expense_recorded` rows.
- New CSV: `expenses_<month>.csv`.

## v0.5 — tax summary exports

- Owner-gated: emit `accounting.export.created` with
  `requires_approval=true` until owner approves the CSV.
- Per-jurisdiction tax buckets.

## v0.6 — weekly / monthly digests

- `accounting.daily_close` events are themselves an event log; weekly
  and monthly digests are second-order summaries over that log.

## Out of scope (probably forever)

- Payment processor integrations.
- Cloud accountant push (we export CSVs; humans push).
- Bookkeeping system replacement.
- Customer-identifying records.
