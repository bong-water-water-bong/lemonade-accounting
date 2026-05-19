# Security

## Reporting a vulnerability

If you find a security issue in Lemonade Accounting, please **do not**
open a public issue. Open a GitHub Security Advisory on this repo
(`Security` tab → `Report a vulnerability`) or contact the
maintainers privately.

We aim to acknowledge reports within a week.

## Threat model (v0.1)

Lemonade Accounting consumes cashier events and emits envelope events.
The threat surface is:

- the published Python package (if/when released to PyPI) — could be
  tampered with;
- the `lemonade-store` GitHub dependency — accounting pins a specific
  tag (`v0.1.0`) and will need to update intentionally;
- the cashier event log on disk — accounting trusts the file contents
  to the extent that `ingest.py` parses them; it does not verify the
  hash chain (that is cashier's `verify` command).

## Privacy boundaries inherited from the suite

- No customer card data is read or written.
- No customer audio or images.
- The per-transaction CSV records `seq`, `attendant`, and money fields
  only — never customer identifiers.
- Accounting envelope events do not include cart line detail; that
  lives in cashier's log if a dispute needs it.

## Dependencies

Runtime: `lemonade-store` (pinned to a Git tag, no transitive deps).
Dev/docs: pytest, ruff, mypy, mkdocs — widely audited.
