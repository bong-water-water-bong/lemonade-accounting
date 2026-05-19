"""`lemonade-accounting` command-line entry point.

Today the CLI exposes one subcommand:

```
lemonade-accounting close \\
    --events /path/to/cashier/events.jsonl \\
    --date 2026-05-19 \\
    --store-id tie-dye-farms \\
    [--csv /path/to/2026-05-19.csv]
```

`close` prints the `accounting.daily_close` envelope event to stdout
as a single line of JSON, suitable for piping into a store-wide
JSONL log. If `--csv` is given, the per-transaction CSV for that day
is written to disk in parallel.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from lemonade_accounting.closer import daily_close
from lemonade_accounting.csv_export import write_transactions_csv
from lemonade_accounting.ingest import IngestError, read_cashier_events


def _positive_timeout(raw: str) -> float:
    """Argparse type for `--timeout-sec`: finite and > 0."""
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not a number: {raw!r}") from exc
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError(f"must be finite, got {raw!r}")
    if value <= 0:
        raise argparse.ArgumentTypeError(f"must be > 0, got {value}")
    return value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lemonade-accounting")
    subparsers = parser.add_subparsers(dest="command", required=True)

    close = subparsers.add_parser(
        "close",
        help="Summarize cashier events for one UTC day and emit accounting.daily_close",
    )
    close.add_argument("--events", required=True, help="Path to cashier events.jsonl")
    close.add_argument("--date", required=True, help="UTC date in YYYY-MM-DD format")
    close.add_argument("--store-id", required=True, help="Store identifier (e.g. tie-dye-farms)")
    close.add_argument(
        "--csv",
        default=None,
        help="Optional path to write the per-transaction CSV for the day",
    )
    close.add_argument(
        "--timeout-sec",
        type=_positive_timeout,
        default=5.0,
        help="Wall-clock budget for reading the cashier log; must be > 0 (default 5.0)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command != "close":
        parser.print_help()
        return 2

    try:
        target = date.fromisoformat(args.date)
    except ValueError as exc:
        print(f"error: invalid --date: {exc}", file=sys.stderr)
        return 2

    try:
        events = read_cashier_events(args.events, timeout_sec=args.timeout_sec)
    except IngestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    close = daily_close(events, date_utc=target, store_id=args.store_id)
    sys.stdout.write(json.dumps(close.event, sort_keys=True) + "\n")

    if args.csv is not None:
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", encoding="utf-8", newline="") as fh:
            write_transactions_csv(events, fh, date_utc=target)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
