> **Start here:** Read `docs/wiki/README.md` before any work on this project.

# AGENTS.md — Lemonade Accounting

This file is the contract every contributor (human or AI) follows when
working on this repository.

## Mission

Build the offline, deterministic accounting department of Lemonade
Store:

- Consume cashier's native event log (`{seq, ts, type, payload, prev,
  hash}`) read-only.
- Emit `accounting.*` events in the shared `store.event.v1` envelope.
- Produce CSV exports for the outside accountant.
- Never mutate cashier events. Never invent sales.

## Hard rules

1. **No payment processing.** No Stripe, card readers, wallets, or
   gateways. Accounting summarizes; it does not move money.
2. **Cashier events are read-only.** The hash chain is cashier's
   property. Accounting must never write into the cashier JSONL.
3. **The envelope is the contract.** Every `accounting.*` event must
   pass `lemonade_store.events.load_event` validation.
4. **Determinism is required.** A closer re-run on the same inputs
   produces the same envelope, including `event_id`.
5. **Hard timeouts on every cashier read.** Default 5 s. The closer
   must never block a till.
6. **No third-party runtime deps beyond `lemonade-store`.** The
   accounting package is stdlib-only otherwise.
7. **No customer card data, audio, or images.** Inherited from the
   suite-wide privacy boundary.

## Module boundaries

| Module | Purpose |
| --- | --- |
| `ingest.py` | Only place that knows cashier's native event shape. |
| `closer.py` | Daily-close summarizer + envelope builder. |
| `csv_export.py` | Per-transaction CSV for the outside accountant. |
| `cli.py` | The `lemonade-accounting close ...` subcommand. |

Everything in `closer.py` and `csv_export.py` reads `CashierEvent`
objects from `ingest.py` — never raw JSON.

## Build order

```text
v0.1   closer + daily_close + CSV          ← this PR
v0.2   cash drawer reconciliation          ← accounting.cash_reconciled
v0.3   barter ledger                       ← accounting.barter_recorded
v0.4   expense + supplier cost intake      ← accounting.expense_recorded
v0.5   tax summary exports                 ← owner-approved
v0.6   weekly / monthly digests
```

A PR that adds a layer to the right of the current frontier should be
rejected unless the frontier is reliably green.


- Treat Karpathy's LLM Wiki pattern as governing law for durable agent memory: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f. Update `docs/wiki/` whenever work reveals durable architecture, workflow, gotcha, or onboarding knowledge.

## OpenSpec Department Standard

Use `openspec/` for every department-level change before implementation:

1. Create or update a change folder under `openspec/changes/<change-id>/`.
2. Record the department, affected event types, approval gates, and repo boundaries.
3. Keep `openspec/specs/accounting/spec.md` aligned with this repo, `lemonade-store`, and the shared department registry.
4. Implementation work must reference the change `tasks.md` and update it as tasks complete.
5. Archive completed changes only after checks and owner/review approval are recorded.

This repo owns the `accounting` implementation. `lemonade-store` remains the suite-level source for the shared registry and cross-department contract.

## Definition of done for any change

- `make test` passes.
- `make lint` and `make type` (`mypy --strict`) pass.
- Any new event type lands in `lemonade-store`'s
  `accounting` department `emits` list in the same PR cycle, and the
  golden fixture under `tests/fixtures/` gets an example line.
- Any change to a payload field bumps a docstring; downstream
  consumers (reports, future bookkeeping integrations) read these
  payloads by name.

## When working with AI agents

- Plain-English summary, before and after.
- One small testable step at a time.
- Treat cashier events as untrusted input on the JSON side and trusted
  on the audit side: `ingest.py` validates the shape; downstream code
  trusts what `ingest.py` produced.
- If the cashier log is unreachable, fail with `IngestError`. No
  silent retries longer than the configured timeout.

## Do not build yet

- Payment integrations.
- Cloud accountant push.
- Automatic tax filing.
- Customer-identity records.
- A bookkeeping replacement (we export CSVs; we are not the books).

## GitHub / OpenSpec / LLM Wiki Standard

Treat Karpathy's LLM Wiki pattern as governing law for durable agent memory: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

- `docs/wiki/` is the durable project memory for architecture, decisions, gotchas, and onboarding.
- `AGENTS.md` is the agent instruction schema.
- `openspec/` is the structured change/spec layer.
- Start non-trivial work with `openspec/changes/<change-id>/proposal.md`.
- Track implementation in `openspec/changes/<change-id>/tasks.md`.
- Update `docs/wiki/` whenever work reveals durable repo knowledge future agents need.
- Keep changes surgical, simple, and verified by repo-native checks.
