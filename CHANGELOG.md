# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-05-19

### Added

- `ingest.py`: read cashier's native JSONL event log into typed
  `CashierEvent` objects with a wall-clock-bounded reader.
- `closer.py`: `daily_close(events, date_utc, store_id) → DailyClose`.
  Filters cashier events to one UTC day, computes a `Summary` with
  `Decimal` totals, and emits a deterministic `accounting.daily_close`
  envelope event in the `store.event.v1` shape.
- `csv_export.py`: per-transaction CSV (`date, seq, attendant, total,
  cash_tendered, change`) for the outside accountant.
- `cli.py`: `lemonade-accounting close ...` subcommand.
- Tests with a golden 14-line cashier fixture covering transactions,
  CIT events, and date-boundary cases.
- Cashier-grade hygiene: pyproject (ruff + mypy strict), Makefile,
  GitHub Actions CI, mkdocs, `CONTRIBUTING`, `CODE_OF_CONDUCT`,
  `SECURITY`, `CODEOWNERS`.

[Unreleased]: https://github.com/bong-water-water-bong/lemonade-accounting/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/bong-water-water-bong/lemonade-accounting/releases/tag/v0.1.0
