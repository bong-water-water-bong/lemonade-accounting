# Lemonade Accounting

The `accounting` department of
[Lemonade Store](https://github.com/bong-water-water-bong/lemonade-store).

This site documents how the closer agent turns cashier-native events
into envelope events and CSV exports.

## Start here

- [Closer](CLOSER.md) — the daily-close summarizer.
- [Events](EVENTS.md) — `accounting.*` event payloads.
- [CSV export](CSV_EXPORT.md) — what the outside accountant gets.
- [Build order](BUILD_ORDER.md) — what comes after v0.1.

## Hard rules in 20 seconds

1. Cashier events are read-only.
2. Determinism is required.
3. Hard timeouts on every read.
4. Envelope is the contract.
5. No payment processing. No cloud requirement.
