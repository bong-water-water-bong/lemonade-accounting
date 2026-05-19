# CSV export

The outside accountant gets a CSV per day with one row per closed
transaction. Columns are stable, in this order:

```text
date,seq,attendant,total,cash_tendered,change
```

| Column | Source |
| --- | --- |
| `date` | The UTC date the `--date` flag was given |
| `seq` | Cashier's monotonically increasing sequence number for the `transaction.tender` event |
| `attendant` | The most recent `transaction.open.payload.attendant` before this tender |
| `total` | `transaction.tender.payload.total` (Decimal as string) |
| `cash_tendered` | `transaction.tender.payload.tender` (Decimal as string) |
| `change` | `transaction.tender.payload.change` (Decimal as string) |

## Example

```csv
date,seq,attendant,total,cash_tendered,change
2026-05-18,3,alice,1.50,5.00,3.50
2026-05-18,7,alice,3.49,4.00,0.51
```

## Spreadsheet-formula safety

Cells whose first character is one of `= + - @ \t \r` are prefixed
with a single quote (`'`) before writing. Spreadsheet apps interpret
those leading characters as a formula; the apostrophe disables
formula parsing and renders the cell as plain text. The attendant
field is the realistic vector (cashier-influenced); the money fields
are sanitized too as defense in depth.

## Privacy

The CSV records:

- `seq` (a cashier-internal number, not a customer identifier)
- `attendant` (employee identifier)
- money fields

It records:

- **No** customer name.
- **No** card or wallet identifier (none exist — the suite is cash-only).
- **No** cart line detail (that lives in cashier's log if a dispute
  needs it).
