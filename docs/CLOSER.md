# Closer

The `closer` agent reads a cashier `events.jsonl`, filters to one UTC
day, and produces:

- a `Summary` (dataclass with `Decimal` totals), and
- an `accounting.daily_close` envelope event in `store.event.v1` shape.

## What the closer summarizes

| Field | Source cashier events | Aggregation |
| --- | --- | --- |
| `transactions_opened` | `transaction.open` | count |
| `transactions_closed` | `transaction.close` | count |
| `sales_total` | `transaction.tender.payload.total` | sum (Decimal) |
| `cash_tendered_total` | `transaction.tender.payload.tender` | sum (Decimal) |
| `change_total` | `transaction.tender.payload.change` | sum (Decimal) |
| `cit_drops` | `cit.drop` | count |
| `cit_pickups` | `cit.pickup` | count |
| `cit_bags_sealed` | `cit.bag.sealed` | count |
| `cit_bags_handed_off` | `cit.bag.handoff` | count |
| `cit_bags_received` | `cit.bag.received` | count |

`cart.*` events are not summarized at the daily-close level; they show
up per-transaction in the CSV export.

## Determinism

`event_id` is derived from `(store_id, date, payload)` via SHA-256.
Re-running the closer on the same cashier log for the same day
produces the exact same envelope event byte-for-byte, including the
`event_id`. That property lets accounting events be appended idempotently
to a store-wide log without de-duping logic.

The envelope `ts` is midnight UTC of the closed day, not the wall-clock
time of the close run. Real run-time lives in the cashier audit log if
anyone needs it.

## Timeout

The cashier-log read has a wall-clock budget (default 5 s) so a slow
disk or network mount can't wedge a close. Pass `--timeout-sec` to the
CLI or `timeout_sec=` to `read_cashier_events()` to tune.

## What the closer does NOT do

- Verify the cashier hash chain. That is `cashier verify`'s job.
- Mutate cashier events.
- Process payments.
- Decide tax.
- Write a CSV by default (it only writes when `--csv PATH` is passed).
