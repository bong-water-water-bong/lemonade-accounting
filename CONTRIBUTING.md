# Contributing

Thanks for taking a look. Lemonade Accounting is small on purpose;
v0.1 is one agent (`closer`), one export (CSV), and one CLI. The bar
for contributions is correctness and clarity.

## Ground rules

- Read [`AGENTS.md`](AGENTS.md) first.
- One logical change per PR.
- `make all` must pass (lint, type, test).
- Conventional Commits (`feat`, `fix`, `docs`, `chore`, `refactor`,
  `test`, `build`, `ci`).
- Branch from `main`; squash-merge; delete the branch on merge.

## Local setup

```sh
git clone https://github.com/bong-water-water-bong/lemonade-accounting
cd lemonade-accounting
make install
make all
```

Python 3.11+ is required. The lone runtime dependency
(`lemonade-store`) is pulled from GitHub by `pip install -e .`.

## Adding a new accounting event type

1. Add the type to `lemonade-store`'s `accounting` department `emits`
   list (separate PR if you need to bump the store version).
2. Implement the agent that emits it. Keep `ingest.py` as the only
   place that knows cashier's event shape.
3. Add a fixture under `tests/fixtures/` and a test in
   `tests/test_<area>.py`.
4. Update `docs/EVENTS.md` and `docs/BUILD_ORDER.md`.

## Adding a CSV export

1. New module under `src/lemonade_accounting/` (one purpose per
   module: `csv_export.py` is per-transaction; future exports should
   live in `csv_<thing>.py`).
2. Stable column order declared as a module-level constant. Add a
   test that pins the column list.
3. CSV row-counts are tested against fixtures, not eyeballed.

## What not to add

- Payment / wallet / card paths.
- A cloud requirement for any accounting workflow.
- A new framework where stdlib already works.
- Anything that depends on a particular SQLite schema; we read events,
  not databases.
