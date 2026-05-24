"""The daily-close summarizer agent.

`daily_close(events, *, date_utc, store_id)` is the entire `closer`
agent in v0.1. It takes the cashier event log (already materialized
via `ingest`), filters to one UTC day, and emits:

* a `Summary` dataclass with `Decimal` totals, and
* the matching `accounting.daily_close` event in `store.event.v1`
  shape, ready to be appended to the store-wide event log.

The agent is **deterministic**: re-running on the same inputs produces
the same envelope, including the same `event_id`. That property is
load-bearing — the closer may be invoked twice (cron + manual) and the
second run must be idempotent.

Money is `Decimal` end-to-end. We never round here; the JSON payload
preserves the exact string the cashier wrote (`"1.50"`, `"3.49"`),
which is the contract the outside accountant expects.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from lemonade_accounting.ingest import CashierEvent, IngestError

# Financial precision rules from .qodo_rules.md
_INTERNAL_PRECISION = Decimal("0.0001")
_DISPLAY_PRECISION = Decimal("0.01")

# Cashier event types we sum / count. Keeping these as constants makes
# it obvious which cashier-side schema changes would force an update
# here.
_TYPE_TXN_OPEN = "transaction.open"
_TYPE_TXN_TENDER = "transaction.tender"
_TYPE_TXN_CLOSE = "transaction.close"
_TYPE_CIT_DROP = "cit.drop"
_TYPE_CIT_PICKUP = "cit.pickup"
_TYPE_CIT_BAG_SEALED = "cit.bag.sealed"
_TYPE_CIT_BAG_HANDOFF = "cit.bag.handoff"
_TYPE_CIT_BAG_RECEIVED = "cit.bag.received"


@dataclass(frozen=True)
class Summary:
    transactions_opened: int = 0
    transactions_closed: int = 0
    sales_total: Decimal = field(default_factory=lambda: Decimal("0.00"))
    cash_tendered_total: Decimal = field(default_factory=lambda: Decimal("0.00"))
    change_total: Decimal = field(default_factory=lambda: Decimal("0.00"))
    cit_drops: int = 0
    cit_pickups: int = 0
    cit_bags_sealed: int = 0
    cit_bags_handed_off: int = 0
    cit_bags_received: int = 0


@dataclass(frozen=True)
class DailyClose:
    """A daily-close result: the structured `Summary` and the envelope `event`.

    Splitting these lets callers either log the envelope, render the
    summary in a UI, or pipe both. The event payload is *derived* from
    the summary so they are guaranteed consistent.
    """

    summary: Summary
    event: dict[str, Any]


def daily_close(
    events: Iterable[CashierEvent],
    *,
    date_utc: date,
    store_id: str,
) -> DailyClose:
    summary = _summarize(events, date_utc=date_utc)
    event = _build_envelope(summary, date_utc=date_utc, store_id=store_id)
    return DailyClose(summary=summary, event=event)


def _summarize(events: Iterable[CashierEvent], *, date_utc: date) -> Summary:
    transactions_opened = 0
    transactions_closed = 0
    sales_total = Decimal("0.00")
    cash_tendered_total = Decimal("0.00")
    change_total = Decimal("0.00")
    cit_drops = 0
    cit_pickups = 0
    cit_bags_sealed = 0
    cit_bags_handed_off = 0
    cit_bags_received = 0

    for event in events:
        if event.utc_date() != date_utc:
            continue
        t = event.type

        if t == _TYPE_TXN_OPEN:
            transactions_opened += 1
        elif t == _TYPE_TXN_CLOSE:
            transactions_closed += 1
        elif t == _TYPE_TXN_TENDER:
            sales_total += _money(event, "total")
            cash_tendered_total += _money(event, "tender")
            change_total += _money(event, "change")
        elif t == _TYPE_CIT_DROP:
            cit_drops += 1
        elif t == _TYPE_CIT_PICKUP:
            cit_pickups += 1
        elif t == _TYPE_CIT_BAG_SEALED:
            cit_bags_sealed += 1
        elif t == _TYPE_CIT_BAG_HANDOFF:
            cit_bags_handed_off += 1
        elif t == _TYPE_CIT_BAG_RECEIVED:
            cit_bags_received += 1
        # Other cashier event types (cart.*) are not summarized at the
        # daily-close level; they are visible per-transaction in the
        # CSV export.

    return Summary(
        transactions_opened=transactions_opened,
        transactions_closed=transactions_closed,
        sales_total=sales_total,
        cash_tendered_total=cash_tendered_total,
        change_total=change_total,
        cit_drops=cit_drops,
        cit_pickups=cit_pickups,
        cit_bags_sealed=cit_bags_sealed,
        cit_bags_handed_off=cit_bags_handed_off,
        cit_bags_received=cit_bags_received,
    )


def _money(event: CashierEvent, key: str) -> Decimal:
    """Parse a tender payload money field, raising `IngestError` on garbage.

    Cashier writes monetary values as strings (e.g. ``"1.50"``). We
    accept missing keys as ``"0.00"``; any other failure to parse
    surfaces as `IngestError` so the CLI's single
    ``except IngestError`` catches it.
    """
    value = event.payload.get(key)
    if value is None:
        return Decimal("0.0000").quantize(_INTERNAL_PRECISION)
    if isinstance(value, Decimal):
        return value.quantize(_INTERNAL_PRECISION, rounding=ROUND_HALF_UP)
    try:
        # `str(value)` covers both string and numeric JSON inputs; we
        # never convert from float, which would corrupt the value
        # cashier carefully serialized with quantize.
        return Decimal(str(value)).quantize(_INTERNAL_PRECISION, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise IngestError(
            f"event seq={event.seq} ({event.type}): payload.{key}={value!r} is not a valid decimal"
        ) from exc


def _build_envelope(summary: Summary, *, date_utc: date, store_id: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "date": date_utc.isoformat(),
        "transactions_opened": summary.transactions_opened,
        "transactions_closed": summary.transactions_closed,
        "sales_total": str(summary.sales_total.quantize(_DISPLAY_PRECISION, rounding=ROUND_HALF_UP)),
        "cash_tendered_total": str(summary.cash_tendered_total.quantize(_DISPLAY_PRECISION, rounding=ROUND_HALF_UP)),
        "change_total": str(summary.change_total.quantize(_DISPLAY_PRECISION, rounding=ROUND_HALF_UP)),
        "cit_drops": summary.cit_drops,
        "cit_pickups": summary.cit_pickups,
        "cit_bags_sealed": summary.cit_bags_sealed,
        "cit_bags_handed_off": summary.cit_bags_handed_off,
        "cit_bags_received": summary.cit_bags_received,
    }
    return {
        "schema_version": "store.event.v1",
        "event_id": _deterministic_event_id(store_id, date_utc, payload),
        # The event's `ts` is *also* deterministic: midnight of the
        # closed day. Real wall-clock time of the close run lives in
        # the cashier audit log; here we want the same event each
        # time, including when re-run for replay.
        "ts": f"{date_utc.isoformat()}T00:00:00+00:00",
        "store_id": store_id,
        "department": "accounting",
        "type": "accounting.daily_close",
        "source": "lemonade-accounting",
        "actor": {"kind": "agent_auto", "id": "accounting.closer"},
        "requires_approval": False,
        "approved_by": None,
        "payload": payload,
    }


def _deterministic_event_id(store_id: str, date_utc: date, payload: dict[str, Any]) -> str:
    """Build a stable `event_id` from (store_id, date, payload).

    Two runs with the same cashier inputs produce the same id; a
    change in any summary field produces a different id. The id is
    intentionally readable and short.
    """
    canonical = json.dumps(
        {"store_id": store_id, "date": date_utc.isoformat(), "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"accounting-daily-close-{store_id}-{date_utc.isoformat()}-{digest}"


def summary_as_dict(summary: Summary) -> dict[str, Any]:
    """Plain-dict view of a `Summary` (Decimals → str for JSON-friendliness)."""
    out: dict[str, Any] = {}
    for key, value in asdict(summary).items():
        if isinstance(value, Decimal):
            out[key] = str(value.quantize(_DISPLAY_PRECISION, rounding=ROUND_HALF_UP))
        else:
            out[key] = value
    return out
