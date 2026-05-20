# Events

All events emitted by `lemonade-accounting` use the `store.event.v1`
envelope from
[`lemonade-store`](https://github.com/bong-water-water-bong/lemonade-store).

The `accounting` department's event namespace is `accounting.*`.

## `accounting.daily_close`

Emitted once per closed UTC day per store. Idempotent: same inputs →
same `event_id`.

### Envelope shape

```json
{
  "schema_version": "store.event.v1",
  "event_id": "accounting-daily-close-tie-dye-farms-2026-05-18-<hash>",
  "ts": "2026-05-18T00:00:00+00:00",
  "store_id": "tie-dye-farms",
  "department": "accounting",
  "type": "accounting.daily_close",
  "source": "lemonade-accounting",
  "actor": { "kind": "agent_auto", "id": "accounting.closer" },
  "requires_approval": false,
  "approved_by": null,
  "payload": {
    "date": "2026-05-18",
    "transactions_opened": 2,
    "transactions_closed": 2,
    "sales_total": "4.99",
    "cash_tendered_total": "9.00",
    "change_total": "4.01",
    "cit_drops": 1,
    "cit_pickups": 0,
    "cit_bags_sealed": 1,
    "cit_bags_handed_off": 1,
    "cit_bags_received": 0
  }
}
```

### Payload contract

| Field | Type | Notes |
| --- | --- | --- |
| `date` | string `YYYY-MM-DD` | UTC date the close is for |
| `transactions_opened` | int | count of `transaction.open` |
| `transactions_closed` | int | count of `transaction.close` |
| `sales_total` | string (Decimal) | sum of tendered `total` |
| `cash_tendered_total` | string (Decimal) | sum of tendered `tender` |
| `change_total` | string (Decimal) | sum of tendered `change` |
| `cit_drops` | int | count of `cit.drop` |
| `cit_pickups` | int | count of `cit.pickup` |
| `cit_bags_sealed` | int | count of `cit.bag.sealed` |
| `cit_bags_handed_off` | int | count of `cit.bag.handoff` |
| `cit_bags_received` | int | count of `cit.bag.received` |

Money fields are **strings**, never floats. They preserve the exact
`Decimal` quantization cashier wrote.

## Future event types

- `accounting.cash_reconciled` — drawer count vs expected.
- `accounting.barter_recorded` — barter ledger entry.
- `accounting.expense_recorded` — supplier or operating expense.
- `accounting.export.created` — CSV export receipt.

See [build order](BUILD_ORDER.md).
