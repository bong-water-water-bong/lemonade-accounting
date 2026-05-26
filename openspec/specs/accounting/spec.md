# Accounting Department Spec

Status: active
Department repo: `lemonade-accounting`
Suite registry: `lemonade-store/src/lemonade_store/departments.py`

## Namespace

`accounting.*`

## Owns

daily close, cash reconciliation, CIT reconciliation, barter ledger, expenses, supplier costs, tax summaries, and CSV exports.

## Consumes

cashier.transaction.closed, cashier.cit.bag.received, cashier.barter.recorded, supplier.order.received, inventory.adjusted.

## Emits

accounting.daily_close, accounting.cash_reconciled, accounting.barter_recorded, accounting.expense_recorded, accounting.export.created.

## Owner Approval

exports and tax filing summaries require owner approval.

## Must Not

rewrite closed cashier transactions, invent sales, or process payments.

## Change Rules

- Changes to consumed/emitted events must be reflected in `lemonade-store`.
- Event-shape changes must include examples and tests in this repo.
- Public, financial, deployment, export, publish, and purchase-order side effects must remain owner-gated.
