"""Tests for the `lemonade-accounting` CLI.

The CLI is the operator interface: point it at a cashier JSONL and a
date, get a daily-close envelope (JSON) on stdout and an optional CSV
written to disk.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from lemonade_accounting.cli import main

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ONE_DAY = FIXTURES / "one_day_cashier.jsonl"


class TestCloseCommand:
    def test_close_prints_envelope_json(self, capsys, tmp_path: Path) -> None:
        rc = main(
            [
                "close",
                "--events",
                str(ONE_DAY),
                "--date",
                "2026-05-18",
                "--store-id",
                "tie-dye-farms",
            ]
        )
        assert rc == 0
        out = capsys.readouterr().out
        event = json.loads(out)
        assert event["department"] == "accounting"
        assert event["type"] == "accounting.daily_close"
        assert event["payload"]["transactions_closed"] == 2

    def test_close_with_csv_writes_file(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "tx.csv"
        rc = main(
            [
                "close",
                "--events",
                str(ONE_DAY),
                "--date",
                "2026-05-18",
                "--store-id",
                "tie-dye-farms",
                "--csv",
                str(csv_path),
            ]
        )
        assert rc == 0
        contents = csv_path.read_text()
        assert "date,seq,attendant,total,cash_tendered,change" in contents
        # 2 transactions => header + 2 rows
        assert contents.count("\n") == 3


class TestCLIBadArgs:
    def test_bad_date_exits_nonzero(self, capsys) -> None:
        rc = main(
            [
                "close",
                "--events",
                str(ONE_DAY),
                "--date",
                "not-a-date",
                "--store-id",
                "tie-dye-farms",
            ]
        )
        assert rc != 0

    def test_missing_events_file_exits_nonzero(self, tmp_path: Path) -> None:
        rc = main(
            [
                "close",
                "--events",
                str(tmp_path / "nope.jsonl"),
                "--date",
                "2026-05-18",
                "--store-id",
                "tie-dye-farms",
            ]
        )
        assert rc != 0


class TestEntryPoint:
    def test_module_runs_as_subprocess(self) -> None:
        # The `lemonade-accounting` script alias is wired in
        # pyproject.toml; this exercises it via `python -m`.
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lemonade_accounting",
                "close",
                "--events",
                str(ONE_DAY),
                "--date",
                "2026-05-18",
                "--store-id",
                "tie-dye-farms",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        event = json.loads(result.stdout)
        assert event["payload"]["transactions_closed"] == 2
