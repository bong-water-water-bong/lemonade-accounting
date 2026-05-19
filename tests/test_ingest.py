"""Tests for cashier-JSONL ingestion.

`ingest` is the boundary between cashier's native event-log shape
(`{seq, ts, type, payload, prev, hash}`) and the rest of accounting.
Every accounting module reads cashier events through `ingest`, never
by parsing JSON itself. That keeps the cashier-format coupling in one
file.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from lemonade_accounting.ingest import (
    CashierEvent,
    IngestError,
    iter_cashier_events,
    read_cashier_events,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ONE_DAY = FIXTURES / "one_day_cashier.jsonl"


class TestReadCashierEvents:
    def test_yields_all_events(self) -> None:
        events = read_cashier_events(ONE_DAY)
        assert len(events) == 14
        assert all(isinstance(e, CashierEvent) for e in events)

    def test_event_fields_typed(self) -> None:
        events = read_cashier_events(ONE_DAY)
        first = events[0]
        assert first.seq == 1
        assert first.ts == "2026-05-18T14:00:00+00:00"
        assert first.type == "transaction.open"
        assert first.payload == {"attendant": "alice", "tax_rate": "0.0875"}

    def test_iter_returns_same_count(self) -> None:
        n = sum(1 for _ in iter_cashier_events(ONE_DAY))
        assert n == 14


class TestFilterByDate:
    def test_filter_one_utc_day(self) -> None:
        events = [e for e in read_cashier_events(ONE_DAY) if e.utc_date() == date(2026, 5, 18)]
        # 11 events fall on 2026-05-18 UTC; 3 fall on 2026-05-19
        assert len(events) == 11

    def test_utc_date_helper(self) -> None:
        events = read_cashier_events(ONE_DAY)
        assert events[0].utc_date() == date(2026, 5, 18)
        assert events[-1].utc_date() == date(2026, 5, 19)


class TestMalformedLines:
    def test_blank_lines_skipped(self, tmp_path: Path) -> None:
        p = tmp_path / "events.jsonl"
        p.write_text(
            ONE_DAY.read_text() + "\n   \n",  # trailing whitespace lines
            encoding="utf-8",
        )
        assert len(read_cashier_events(p)) == 14

    def test_corrupt_line_raises_ingest_error(self, tmp_path: Path) -> None:
        p = tmp_path / "events.jsonl"
        p.write_text("not-json\n", encoding="utf-8")
        with pytest.raises(IngestError):
            read_cashier_events(p)

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "events.jsonl"
        p.write_text('{"seq":1,"type":"x"}\n', encoding="utf-8")
        with pytest.raises(IngestError):
            read_cashier_events(p)


class TestCoercionErrorsAreIngestErrors:
    """`int(record['seq'])` and friends must not leak as raw exceptions."""

    def test_seq_not_an_integer_raises_ingest_error(self, tmp_path: Path) -> None:
        p = tmp_path / "events.jsonl"
        # `seq` is a list — `int([...])` raises TypeError.
        p.write_text(
            '{"seq":[1,2],"ts":"2026-05-18T14:00:00+00:00","type":"x.y",'
            '"payload":{},"prev":"a","hash":"b"}\n',
            encoding="utf-8",
        )
        with pytest.raises(IngestError) as exc:
            read_cashier_events(p)
        assert "invalid field types" in str(exc.value)

    def test_payload_not_a_dict_raises_ingest_error(self, tmp_path: Path) -> None:
        p = tmp_path / "events.jsonl"
        p.write_text(
            '{"seq":1,"ts":"2026-05-18T14:00:00+00:00","type":"x.y",'
            '"payload":"not-an-object","prev":"a","hash":"b"}\n',
            encoding="utf-8",
        )
        with pytest.raises(IngestError) as exc:
            read_cashier_events(p)
        assert "payload" in str(exc.value).lower()


class TestUtcDateNormalization:
    def test_z_suffix_accepted(self) -> None:
        from lemonade_accounting.ingest import CashierEvent

        event = CashierEvent(
            seq=1,
            ts="2026-05-18T23:30:00Z",
            type="x.y",
            payload={},
            prev="a",
            hash="b",
        )
        assert event.utc_date() == date(2026, 5, 18)

    def test_non_utc_offset_normalized_to_utc(self) -> None:
        from lemonade_accounting.ingest import CashierEvent

        # 23:30-08:00 = 07:30+00:00 the *next* day; the UTC bucket is
        # the one that matters for daily close.
        event = CashierEvent(
            seq=1,
            ts="2026-05-18T23:30:00-08:00",
            type="x.y",
            payload={},
            prev="a",
            hash="b",
        )
        assert event.utc_date() == date(2026, 5, 19)


class TestReadTimeout:
    def test_timeout_zero_rejects_long_read(self, tmp_path: Path) -> None:
        # A 0-second budget is the simplest deterministic way to prove
        # the timeout fires; production callers pass something like 5.0.
        p = tmp_path / "events.jsonl"
        p.write_text(ONE_DAY.read_text(), encoding="utf-8")
        with pytest.raises(IngestError) as exc:
            read_cashier_events(p, timeout_sec=0.0)
        assert "timeout" in str(exc.value).lower()
