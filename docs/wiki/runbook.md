# Runbook & Start Procedures

This document provides instructions on how to set up the development environment, execute automated verification gates, run the command-line interface (CLI), and troubleshoot common issues.

## Environment Setup

1. **Python Version**: Ensure Python `3.11` or higher is installed and active in your terminal (derived from the `requires-python` constraint in [pyproject.toml](../../pyproject.toml#L10)).
2. **Install Package**: Run the following command inside the repository root to perform an editable installation of `lemonade-accounting` alongside developer and documentation dependencies (defined in `[project.optional-dependencies]` in [pyproject.toml](../../pyproject.toml#L33-L43)):
   ```bash
   make install
   ```
   *(Alternative: `python3 -m pip install -e ".[dev,docs]"`; both commands install the optional `dev` and `docs` dependency groups from [pyproject.toml](../../pyproject.toml#L33-L43))*

## Verification Gates

Always run the full suite of verification checks before opening a pull request:

```bash
make lint    # Run code styling checks (Ruff)
make type    # Run strict static typing analysis (Mypy)
make test    # Run pytest test suite
```

### Coverage Reports
To view statement coverage statistics and pinpoint untested blocks:
```bash
make test-cov
```

### Automatic Code Formatting
To format the python source files according to the Ruff guidelines:
```bash
make fmt
```
*(Note: Import sorting is governed by the `I` ruleset in [pyproject.toml](../../pyproject.toml#L73) and is performed via `ruff check --fix` during `make lint`).*

### Documentation Site
To compile the documentation pages statically using MkDocs:
```bash
make docs
```
*(Note: The build executes `mkdocs build --strict` as defined in the [Makefile](../../Makefile#L39). To preview the site interactively with hot-reloading, run `python3 -m mkdocs serve`. Note that agent-facing documents in the `wiki/` directory and `AGENTS.md` are excluded from the MkDocs site generation via `exclude_docs` in [mkdocs.yml](../../mkdocs.yml#L40-L42)).*

---

## Running the CLI

The project provides the command-line utility `lemonade-accounting`.

### The `close` Command

Generates a daily close summary for a single UTC day from a cashier transaction log file.

```bash
lemonade-accounting close \
  --events /path/to/cashier/events.jsonl \
  --date YYYY-MM-DD \
  --store-id <store-id> \
  [--csv /path/to/reconciled.csv] \
  [--timeout-sec 5.0]
```

#### Arguments
- `--events`: (Required) Path to the cashier event log JSONL file.
- `--date`: (Required) Target UTC date to close (format: `YYYY-MM-DD`).
- `--store-id`: (Required) The physical store location identifier (e.g. `tie-dye-farms`).
- `--csv`: (Optional) Output path for a tabular CSV translation of transaction records, processed sequentially in the main thread after stdout is written (defined in [cli.py](../../src/lemonade_accounting/cli.py#L95-L99)).
- `--timeout-sec`: (Optional, default `5.0`) Wall-clock budget in seconds (default `5.0` as defined in [cli.py](../../src/lemonade_accounting/cli.py#L66) and [ingest.py](../../src/lemonade_accounting/ingest.py#L76)). Useful to prevent stalls blocking. To disable, set to a very large number (or set it to `None` if calling `iter_cashier_events` programmatically).

#### Example Execution
```bash
lemonade-accounting close \
  --events tests/fixtures/one_day_cashier.jsonl \
  --date 2026-05-18 \
  --store-id tie-dye-farms \
  --csv output/2026-05-18.csv
```

Outputs the structured `accounting.daily_close` envelope JSON string directly to `stdout`.

---

## Troubleshooting & Failure Modes

- **`error: cashier event log not found: ...`**:
  Verify that the `--events` path exists. The tool raises `IngestError` and exits with status code `1` if the input file does not exist.
- **`error: malformed JSON at ...: ...`**:
  One or more lines in the JSONL log contains invalid JSON syntax. The parser throws `IngestError` detailing the line number.
- **`error: timeout (> 5.0s) reading ... at line ...`**:
  The log reading process exceeded the allotted wall-clock budget. Increase `--timeout-sec` if performing deep history analysis or working with extremely large log dumps.
- **`error: invalid --date: ...`**:
  The provided date string is not in standard ISO format (`YYYY-MM-DD`). Fix the CLI arguments and re-run.

## Related Docs
- [README.md](README.md) — Mission and entry point
- [architecture.md](architecture.md) — System design and pipeline flows
- [conventions.md](conventions.md) — Coding conventions & rules
- [agents.md](agents.md) — Rules, limits, and safe change zones
