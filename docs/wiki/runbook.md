# Runbook & Start Procedures

This document provides instructions on how to set up the development environment, execute automated verification gates, run the command-line interface (CLI), and troubleshoot common issues.

## Environment Setup

1. **Python Version**: Ensure Python `3.11` or higher is installed and active in your terminal.
2. **Install Package**: Run the following command inside the repository root to perform an editable installation of `lemonade-accounting` alongside developer and documentation dependencies:
   ```bash
   make install
   ```
   *(Alternative: `python3 -m pip install -e ".[dev,docs]"`)*

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
To automatically adjust import sorting and resolve style non-conformance:
```bash
make fmt
```

### Documentation Site
To compile and preview the documentation pages using MkDocs:
```bash
make docs
```

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
- `--csv`: (Optional) Output path for a tabular CSV translation of transaction records.
- `--timeout-sec`: (Optional, default `5.0`) Wall-clock budget budget in seconds. Useful to prevent talls blocking. Use a high number or disable (via setting it very large or handled upstream) for long-history replays.

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
- [README.md](file:///home/bcloud/multica_workspaces_desktop-localhost-18088/eb279b7e-f49c-4099-a687-c1af978f0a5d/295c11a5/workdir/lemonade-accounting/docs/wiki/README.md) — Mission and entry point
- [architecture.md](file:///home/bcloud/multica_workspaces_desktop-localhost-18088/eb279b7e-f49c-4099-a687-c1af978f0a5d/295c11a5/workdir/lemonade-accounting/docs/wiki/architecture.md) — System design and pipeline flows
- [conventions.md](file:///home/bcloud/multica_workspaces_desktop-localhost-18088/eb279b7e-f49c-4099-a687-c1af978f0a5d/295c11a5/workdir/lemonade-accounting/docs/wiki/conventions.md) — Coding conventions & rules
- [agents.md](file:///home/bcloud/multica_workspaces_desktop-localhost-18088/eb279b7e-f49c-4099-a687-c1af978f0a5d/295c11a5/workdir/lemonade-accounting/docs/wiki/agents.md) — Rules, limits, and safe change zones
