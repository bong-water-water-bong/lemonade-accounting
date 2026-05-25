"""Tests for the `closer` agent — the daily-close summarizer.

`closer.daily_close(events, *, date_utc, store_id)` returns a
deterministic `Summary` for one UTC day, plus the matching
`accounting.daily_close` envelope event. Both are derived from cashier
events; the closer never mutates them.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from lemonade_store.events import EventValidationError, load_event

from lemonade_accounting.closer import Summary, daily_close
from lemonade_accounting.ingest import read_cashier_events

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ONE_DAY = FIXTURES / "one_day_cashier.jsonl"
ONE_DAY_STORE_EVENTS = FIXTURES / "one_day_cashier_store_events.jsonl"

D = Decimal


def _summary_for(target: date) -> Summary:
    events = read_cashier_events(ONE_DAY)
    return daily_close(events, date_utc=target, store_id="tie-dye-farms").summary


class TestDailyCloseSummary:
    def test_counts_transactions_closed_on_target_day(self) -> None:
        # 2026-05-18 has two closed transactions; 2026-05-19 has one.
        assert _summary_for(date(2026, 5, 18)).transactions_closed == 2
        assert _summary_for(date(2026, 5, 19)).transactions_closed == 1

    def test_sales_total_sums_tendered_totals(self) -> None:
        # tender totals on 2026-05-18: 1.50 + 3.49 = 4.99
        assert _summary_for(date(2026, 5, 18)).sales_total == D("4.99")
        assert _summary_for(date(2026, 5, 19)).sales_total == D("7.42")

    def test_cash_tendered_and_change(self) -> None:
        s = _summary_for(date(2026, 5, 18))
        assert s.cash_tendered_total == D("9.00")  # 5.00 + 4.00
        assert s.change_total == D("4.01")  # 3.50 + 0.51

    def test_cit_drops_and_bags(self) -> None:
        s = _summary_for(date(2026, 5, 18))
        assert s.cit_drops == 1
        assert s.cit_bags_sealed == 1
        assert s.cit_bags_handed_off == 1

    def test_zero_day_summary(self) -> None:
        s = _summary_for(date(2026, 5, 17))
        assert s.transactions_closed == 0
        assert s.sales_total == D("0.00")
        assert s.cash_tendered_total == D("0.00")

    def test_precision_enforcement(self, tmp_path: Path) -> None:
        """Internal 4-place precision must be rounded to 2-place for display/envelope."""
        p = tmp_path / "precision.jsonl"
        # 1.0001 + 1.0001 = 2.0002.
        # Display should be 2.00.
        p.write_text(
            '{"seq":1,"ts":"2026-05-18T14:00:00+00:00","type":"transaction.tender",'
            '"payload":{"total":"1.0001","tender":"2.0000","change":"0.9999"},"prev":"a","hash":"b"}\n',
            encoding="utf-8"
        )
        events = read_cashier_events(p)
        close = daily_close(events, date_utc=date(2026, 5, 18), store_id="test-store")
        
        # Internal summary should have 4 places (if we enforce it)
        # For now, let's see what it has. 
        # Actually, if we WANT to enforce 4 places, we should check for it.
        assert close.summary.sales_total == D("1.0001")
        
        # Envelope payload MUST be 2 places.
        assert close.event["payload"]["sales_total"] == "1.00"
        assert close.event["payload"]["cash_tendered_total"] == "2.00"
        assert close.event["payload"]["change_total"] == "1.00"


class TestEnvelopeEvent:
    def test_envelope_is_valid_store_event_v1(self) -> None:
        events = read_cashier_events(ONE_DAY)
        close = daily_close(events, date_utc=date(2026, 5, 18), store_id="tie-dye-farms")
        # `event` is a dict shaped like store.event.v1; round-trip via
        # the shared loader to confirm contract compliance.
        loaded = load_event(close.event)
        assert loaded.department == "accounting"
        assert loaded.type == "accounting.daily_close"
        assert loaded.store_id == "tie-dye-farms"
        assert loaded.source == "lemonade-accounting"
        assert loaded.requires_approval is False

    def test_envelope_payload_includes_summary_fields(self) -> None:
        events = read_cashier_events(ONE_DAY)
        close = daily_close(events, date_utc=date(2026, 5, 18), store_id="tie-dye-farms")
        payload = close.event["payload"]
        assert payload["date"] == "2026-05-18"
        assert payload["transactions_closed"] == 2
        # Money fields are strings to preserve Decimal precision in JSON.
        assert payload["sales_total"] == "4.99"
        assert payload["cash_tendered_total"] == "9.00"
        assert payload["change_total"] == "4.01"

    def test_event_id_is_deterministic(self) -> None:
        events = read_cashier_events(ONE_DAY)
        close1 = daily_close(events, date_utc=date(2026, 5, 18), store_id="tie-dye-farms")
        close2 = daily_close(events, date_utc=date(2026, 5, 18), store_id="tie-dye-farms")
        # Re-running the closer on the same inputs must produce the
        # same event_id, so accounting events are themselves replayable
        # and don't pile up on idempotent re-runs.
        assert close1.event["event_id"] == close2.event["event_id"]
        # JSON dumps must also match byte-for-byte.
        assert json.dumps(close1.event, sort_keys=True) == json.dumps(close2.event, sort_keys=True)

    def test_event_id_changes_when_summary_changes(self) -> None:
        events = read_cashier_events(ONE_DAY)
        a = daily_close(events, date_utc=date(2026, 5, 18), store_id="tie-dye-farms")
        b = daily_close(events, date_utc=date(2026, 5, 19), store_id="tie-dye-farms")
        assert a.event["event_id"] != b.event["event_id"]

    def test_projected_store_events_produce_same_daily_close(self) -> None:
        native = daily_close(
            read_cashier_events(ONE_DAY),
            date_utc=date(2026, 5, 18),
            store_id="tie-dye-farms",
        )
        projected = daily_close(
            read_cashier_events(ONE_DAY_STORE_EVENTS),
            date_utc=date(2026, 5, 18),
            store_id="tie-dye-farms",
        )

        assert projected.summary.transactions_closed == native.summary.transactions_closed
        assert projected.summary.sales_total == native.summary.sales_total
        assert projected.summary.cash_tendered_total == native.summary.cash_tendered_total
        assert projected.summary.change_total == native.summary.change_total
        assert load_event(projected.event).type == "accounting.daily_close"


class TestCashierEventsAreReadOnly:
    def test_closer_does_not_mutate_input(self) -> None:
        events = read_cashier_events(ONE_DAY)
        snapshot = [(e.seq, e.ts, e.type, dict(e.payload), e.prev, e.hash) for e in events]
        daily_close(events, date_utc=date(2026, 5, 18), store_id="tie-dye-farms")
        after = [(e.seq, e.ts, e.type, dict(e.payload), e.prev, e.hash) for e in events]
        assert snapshot == after


class TestMalformedMoneyRaisesIngestError:
    """Decimal parse failures inside `_summarize` must surface as IngestError."""

    def test_garbage_tender_field_raises(self, tmp_path: Path) -> None:
        from lemonade_accounting.ingest import IngestError, read_cashier_events

        p = tmp_path / "events.jsonl"
        # `total` is "not-money" — Decimal raises InvalidOperation.
        p.write_text(
            '{"seq":1,"ts":"2026-05-18T14:00:00+00:00",'
            '"type":"transaction.tender",'
            '"payload":{"tender":"5.00","total":"not-money","change":"0.00"},'
            '"prev":"a","hash":"b"}\n',
            encoding="utf-8",
        )
        import pytest

        events = read_cashier_events(p)
        with pytest.raises(IngestError) as exc:
            daily_close(events, date_utc=date(2026, 5, 18), store_id="tie-dye-farms")
        assert "decimal" in str(exc.value).lower()
        assert "seq=1" in str(exc.value)


class TestEnvelopeMatchesContract:
    def test_envelope_rejected_if_store_id_missing(self) -> None:
        # Sanity-check: any breakage to our envelope shape would be caught
        # by lemonade-store. This test exists so a future refactor of
        # closer.py that drops a field gets a clear failure here, not in
        # a downstream consumer.
        events = read_cashier_events(ONE_DAY)
        close = daily_close(events, date_utc=date(2026, 5, 18), store_id="tie-dye-farms")
        bad = dict(close.event)
        del bad["store_id"]
        try:
            load_event(bad)
        except EventValidationError:
            return
        raise AssertionError("envelope without store_id should not validate")
