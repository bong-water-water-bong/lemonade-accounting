"""Lemonade Accounting — daily close, cash reconciliation, CSV exports.

This package consumes cashier-native events (the hash-chained JSONL
format defined by `lemonade_cashier.audit.eventlog`) and produces
`store.event.v1` envelope events in the `accounting.*` namespace.

It is intentionally *consumer-only* with respect to cashier events:
the closer never mutates cashier state and never writes a cashier-typed
event. See the AGENTS.md file for the contract.
"""

from lemonade_accounting.closer import DailyClose, Summary, daily_close
from lemonade_accounting.csv_export import (
    TRANSACTION_COLUMNS,
    write_transactions_csv,
)
from lemonade_accounting.ingest import (
    CashierEvent,
    IngestError,
    iter_cashier_events,
    read_cashier_events,
)

__all__ = [
    "CashierEvent",
    "DailyClose",
    "IngestError",
    "Summary",
    "TRANSACTION_COLUMNS",
    "daily_close",
    "iter_cashier_events",
    "read_cashier_events",
    "write_transactions_csv",
]

__version__ = "0.1.0"
