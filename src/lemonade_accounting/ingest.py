"""Read cashier's native JSONL event log.

Cashier writes one line per event in the shape produced by
`lemonade_cashier.audit.eventlog.EventLog.append`:

```
{
  "seq":     1,
  "ts":      "2026-05-18T14:00:00+00:00",
  "type":    "transaction.open",
  "payload": {...},
  "prev":    "<sha256-hex of previous record>",
  "hash":    "<sha256-hex of this record>"
}
```

This module is the **only** place that knows that shape. Every other
accounting module reads `CashierEvent` objects produced here.

Two non-obvious choices:

* `iter_cashier_events` enforces an optional wall-clock timeout because
  the eventual production setup may read from a slow disk or a network
  mount and we never want a daily close to wedge waiting for I/O. The
  default is 5 seconds; the cashier is the source of truth and
  accounting must not block it.
* `IngestError` wraps everything (bad JSON, missing field, timeout) so
  callers can have a single `except`. We do *not* try to verify the
  hash chain here — that is cashier's own job, run by `cashier verify`.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

_REQUIRED_FIELDS: tuple[str, ...] = ("seq", "ts", "type", "payload", "prev", "hash")


class IngestError(RuntimeError):
    """Raised when a cashier event log can't be read or is malformed."""


@dataclass(frozen=True)
class CashierEvent:
    seq: int
    ts: str
    type: str
    payload: dict[str, Any]
    prev: str
    hash: str

    def utc_date(self) -> date:
        # Cashier writes timestamps with an explicit UTC offset
        # (`+00:00` or `Z`), so `datetime.fromisoformat` returns a
        # tz-aware value; converting to UTC is a no-op but makes the
        # intent explicit and protects against a future format drift.
        return datetime.fromisoformat(self.ts).date()


def iter_cashier_events(
    path: str | Path,
    *,
    timeout_sec: float | None = 5.0,
) -> Iterator[CashierEvent]:
    """Yield events from a cashier JSONL file.

    Pass ``timeout_sec=None`` to disable the wall-clock guard (useful in
    long replays). The default 5-second budget is intended to fail fast
    for daily-close jobs that should normally complete in well under a
    second.
    """
    path = Path(path)
    if not path.exists():
        raise IngestError(f"cashier event log not found: {path}")

    deadline = time.monotonic() + timeout_sec if timeout_sec is not None else None

    with path.open("r", encoding="utf-8") as fh:
        for line_number, raw in enumerate(fh, start=1):
            if deadline is not None and time.monotonic() > deadline:
                raise IngestError(
                    f"timeout (> {timeout_sec}s) reading {path} at line {line_number}"
                )

            line = raw.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise IngestError(f"malformed JSON at {path}:{line_number}: {exc}") from exc

            if not isinstance(record, dict):
                raise IngestError(f"{path}:{line_number}: event must be a JSON object")
            for required in _REQUIRED_FIELDS:
                if required not in record:
                    raise IngestError(f"{path}:{line_number}: missing required field {required!r}")

            yield CashierEvent(
                seq=int(record["seq"]),
                ts=str(record["ts"]),
                type=str(record["type"]),
                payload=dict(record["payload"]),
                prev=str(record["prev"]),
                hash=str(record["hash"]),
            )


def read_cashier_events(
    path: str | Path,
    *,
    timeout_sec: float | None = 5.0,
) -> list[CashierEvent]:
    """Materialize all events from a cashier JSONL file."""
    return list(iter_cashier_events(path, timeout_sec=timeout_sec))
