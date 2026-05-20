"""Tests for the CSV export.

The outside accountant gets a CSV per day with one row per closed
transaction. The columns are stable and quoted predictably so a
spreadsheet program reads it without surprises.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from io import StringIO
from pathlib import Path

import pytest

from lemonade_accounting.csv_export import (
    TRANSACTION_COLUMNS,
    write_transactions_csv,
)
from lemonade_accounting.ingest import read_cashier_events

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ONE_DAY = FIXTURES / "one_day_cashier.jsonl"


def _csv_rows(target: date) -> list[dict[str, str]]:
    events = read_cashier_events(ONE_DAY)
    buf = StringIO()
    write_transactions_csv(events, buf, date_utc=target)
    buf.seek(0)
    return list(csv.DictReader(buf))


class TestTransactionsCSV:
    def test_columns_are_stable(self) -> None:
        rows = _csv_rows(date(2026, 5, 18))
        assert list(rows[0].keys()) == list(TRANSACTION_COLUMNS)

    def test_one_row_per_closed_transaction(self) -> None:
        # 2026-05-18 has two `transaction.tender` events.
        assert len(_csv_rows(date(2026, 5, 18))) == 2
        assert len(_csv_rows(date(2026, 5, 19))) == 1

    def test_row_values(self) -> None:
        rows = _csv_rows(date(2026, 5, 18))
        first = rows[0]
        assert first["date"] == "2026-05-18"
        assert first["total"] == "1.50"
        assert first["cash_tendered"] == "5.00"
        assert first["change"] == "3.50"
        assert first["seq"] == "3"
        assert first["attendant"] == "alice"

    def test_zero_day_writes_header_only(self) -> None:
        rows = _csv_rows(date(2026, 5, 17))
        assert rows == []


class TestCSVFormulaInjectionDefense:
    """Cells starting with formula triggers must be neutralized."""

    @pytest.fixture
    def malicious_log(self, tmp_path: Path) -> Path:
        p = tmp_path / "events.jsonl"
        p.write_text(
            # Attendant name starts with `=`; total starts with `+`.
            '{"seq":1,"ts":"2026-05-18T14:00:00+00:00",'
            '"type":"transaction.open",'
            '"payload":{"attendant":"=cmd|\\"/c calc\\"!A1"},'
            '"prev":"a","hash":"b"}\n'
            '{"seq":2,"ts":"2026-05-18T14:01:00+00:00",'
            '"type":"transaction.tender",'
            '"payload":{"tender":"5.00","total":"+1.50","change":"3.50"},'
            '"prev":"b","hash":"c"}\n',
            encoding="utf-8",
        )
        return p

    def test_formula_cells_are_quoted(self, malicious_log: Path) -> None:
        events = read_cashier_events(malicious_log)
        buf = StringIO()
        write_transactions_csv(events, buf, date_utc=date(2026, 5, 18))
        buf.seek(0)
        rows = list(csv.DictReader(buf))
        assert rows[0]["attendant"].startswith("'=")
        assert rows[0]["total"].startswith("'+")

    @pytest.mark.parametrize(
        ("attendant", "total", "expect_attendant_prefix", "expect_total_prefix"),
        [
            # Tab and carriage return as the leading character — Excel
            # treats both as formula triggers in some import paths.
            ("\tlead-tab", "1.00", "'\t", "1"),
            ("\rlead-cr", "1.00", "'\r", "1"),
            # Negative numbers look like a formula to a spreadsheet (it
            # tries to evaluate `-1.50` as `=NEGATE(1.50)`).
            ("alice", "-1.50", "a", "'-"),
            # `@` triggers Excel's intersection operator.
            ("alice", "@sum(1,1)", "a", "'@"),
        ],
    )
    def test_other_formula_triggers_are_quoted(
        self,
        tmp_path: Path,
        attendant: str,
        total: str,
        expect_attendant_prefix: str,
        expect_total_prefix: str,
    ) -> None:
        p = tmp_path / "events.jsonl"
        open_event = {
            "seq": 1,
            "ts": "2026-05-18T14:00:00+00:00",
            "type": "transaction.open",
            "payload": {"attendant": attendant},
            "prev": "a",
            "hash": "b",
        }
        tender_event = {
            "seq": 2,
            "ts": "2026-05-18T14:01:00+00:00",
            "type": "transaction.tender",
            "payload": {"tender": "5.00", "total": total, "change": "3.50"},
            "prev": "b",
            "hash": "c",
        }
        p.write_text(
            json.dumps(open_event) + "\n" + json.dumps(tender_event) + "\n",
            encoding="utf-8",
        )
        events = read_cashier_events(p)
        buf = StringIO()
        write_transactions_csv(events, buf, date_utc=date(2026, 5, 18))
        buf.seek(0)
        row = next(csv.DictReader(buf))
        assert row["attendant"].startswith(expect_attendant_prefix)
        assert row["total"].startswith(expect_total_prefix)
