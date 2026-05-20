"""CSV export for the outside accountant.

One row per `transaction.tender` event on the target UTC day, plus a
stable column order:

```
date,seq,attendant,total,cash_tendered,change
```

The accountant cares about totals and tendered cash, not cart-line
detail; the cart breakdown lives in the cashier audit log and can be
shown there if a dispute ever needs it.

The current attendant is taken from the most recent `transaction.open`
seen before the tender event. That keeps the CSV self-contained
without requiring the closer to remember cashier internals.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import date
from typing import IO

from lemonade_accounting.ingest import CashierEvent

TRANSACTION_COLUMNS: tuple[str, ...] = (
    "date",
    "seq",
    "attendant",
    "total",
    "cash_tendered",
    "change",
)

# Spreadsheet applications (Excel, LibreOffice, Google Sheets) interpret
# a cell that starts with any of these characters as a formula. An
# attendant name like `=cmd|"/c calc"!A1` opens code-execution surface
# the moment the outside accountant double-clicks the CSV. Defuse by
# prefixing a single quote, which spreadsheet apps render as a leading
# apostrophe-text marker without changing the value's meaning.
_FORMULA_PREFIXES: tuple[str, ...] = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value: str) -> str:
    if value and value[0] in _FORMULA_PREFIXES:
        return "'" + value
    return value


def write_transactions_csv(
    events: Iterable[CashierEvent],
    file: IO[str],
    *,
    date_utc: date,
) -> int:
    """Write one CSV row per closed transaction on `date_utc`.

    Returns the number of data rows written (excludes the header).
    """
    writer = csv.DictWriter(file, fieldnames=list(TRANSACTION_COLUMNS))
    writer.writeheader()

    current_attendant: str = ""
    rows_written = 0
    for event in events:
        if event.type == "transaction.open":
            current_attendant = str(event.payload.get("attendant", ""))
            continue
        if event.type != "transaction.tender":
            continue
        if event.utc_date() != date_utc:
            continue

        writer.writerow(
            {
                "date": date_utc.isoformat(),
                "seq": event.seq,
                "attendant": _csv_safe(current_attendant),
                "total": _csv_safe(str(event.payload.get("total", ""))),
                "cash_tendered": _csv_safe(str(event.payload.get("tender", ""))),
                "change": _csv_safe(str(event.payload.get("change", ""))),
            }
        )
        rows_written += 1
    return rows_written
