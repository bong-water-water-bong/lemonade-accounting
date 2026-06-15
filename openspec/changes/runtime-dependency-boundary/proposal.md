# Change Proposal: runtime-dependency-boundary

## Department

- Department: accounting
- Repo: lemonade-accounting
- Namespace: accounting.*

## Why

Accounting is a deterministic, offline department that only needs
`lemonade-store` for shared event contracts at runtime. Requiring
`lemonade-agents` during base install pulls the GAIA/model stack into a
normal accounting setup even when no agent bridge is being used.

## What Changes

- Point the shared contract dependency at `lemonade-store@main`.
- Move `lemonade-agents` from required dependencies to the optional
  `agents` extra.
- Teach the Makefile to create and prefer `.venv` for local development.
- Document the base install versus optional external agent bridge install.

## Affected Events

- Consumes: cashier.*
- Emits: accounting.daily_close

## Approval Gates

- Owner approval required: no
- Approval type: packaging/docs cleanup; no event contract change

## Verification

- [x] `make install`
- [x] `make all`
- [x] `make docs`
