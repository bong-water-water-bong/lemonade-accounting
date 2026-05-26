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

* `iter_cashier_events` enforces an optional wall-clock timeout that
  is checked **between successfully read lines**. It bounds total
  parse time when the file is producing data slowly; it cannot
  interrupt a single OS-level blocked read (a true I/O kill switch
  needs a worker thread, deferred to a future revision). The default
  budget is 5 seconds.
* `IngestError` wraps everything (bad JSON, missing field, type
  coercion failures, timeout) so callers can have a single `except`.
  We do *not* verify the cashier hash chain here — that is cashier's
  own job, run by `cashier verify`.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from lemonade_store.events import EventValidationError, load_event

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
        # (`+00:00`), but the contract also allows `Z`. Python's
        # `datetime.fromisoformat` accepts `Z` on 3.11+, but we
        # normalize anyway to keep the conversion intent explicit
        # and to guard against a future format drift to a non-UTC
        # offset. After normalization we extract the date in UTC.
        ts = self.ts.replace("Z", "+00:00") if self.ts.endswith("Z") else self.ts
        return datetime.fromisoformat(ts).astimezone(UTC).date()


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
            if record.get("schema_version") == "store.event.v1":
                # Is this a hybrid event (store envelope + top-level audit fields)?
                # If it has seq, prev, and hash, it's a native cashier event.
                if all(k in record for k in ("seq", "prev", "hash")):
                    pass # handle normally below
                else:
                    projected = _cashier_event_from_store_envelope(record, path=path, line=line_number)
                    if projected is not None:
                        yield projected
                    continue
            for required in _REQUIRED_FIELDS:
                if required not in record:
                    raise IngestError(f"{path}:{line_number}: missing required field {required!r}")

            if not isinstance(record["payload"], dict):
                raise IngestError(
                    f"{path}:{line_number}: payload must be a JSON object, "
                    f"got {type(record['payload']).__name__}"
                )

            # Type coercion failures (e.g. seq is a list, ts is null)
            # must surface as `IngestError` so the CLI's single
            # `except IngestError` catches them. Without this guard the
            # bare `int(...)` / `str(...)` calls below leak
            # `TypeError` / `ValueError` to the caller.
            try:
                yield CashierEvent(
                    seq=int(record["seq"]),
                    ts=str(record["ts"]),
                    type=str(record["type"]),
                    payload=dict(record["payload"]),
                    prev=str(record["prev"]),
                    hash=str(record["hash"]),
                )
            except (TypeError, ValueError) as exc:
                raise IngestError(f"{path}:{line_number}: invalid field types: {exc}") from exc


def _cashier_event_from_store_envelope(
    record: dict[str, Any],
    *,
    path: Path,
    line: int,
) -> CashierEvent | None:
    try:
        event = load_event(record)
    except EventValidationError as exc:
        raise IngestError(f"{path}:{line}: invalid store.event.v1 envelope: {exc}") from exc

    if event.department != "cashier":
        return None

    payload = dict(event.payload)
    original_seq = payload.get("original_seq", 0)
    original_prev = payload.get("original_prev", "")
    original_hash = payload.get("original_hash", event.event_id)
    try:
        seq = int(original_seq)
    except (TypeError, ValueError) as exc:
        raise IngestError(
            f"{path}:{line}: payload.original_seq={original_seq!r} is not an integer"
        ) from exc

    return CashierEvent(
        seq=seq,
        ts=event.ts,
        type=event.type,
        payload=payload,
        prev=str(original_prev),
        hash=str(original_hash),
    )


def read_cashier_events(
    path: str | Path,
    *,
    timeout_sec: float | None = 5.0,
) -> list[CashierEvent]:
    """Materialize all events from a cashier JSONL file."""
    return list(iter_cashier_events(path, timeout_sec=timeout_sec))
