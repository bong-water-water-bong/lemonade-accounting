# Lemonade Accounting — convenience targets.

VENV_PYTHON := .venv/bin/python
PYTHON ?= $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),python3)

.PHONY: all help venv install install-agents test test-cov lint type fmt docs clean

all: lint type test

help:
	@echo "Targets:"
	@echo "  make venv        Create .venv with python3"
	@echo "  make install     Install the package (editable) with dev extras"
	@echo "  make install-agents Install optional external agent bridge packages"
	@echo "  make test        Run the test suite"
	@echo "  make test-cov    Run tests with coverage"
	@echo "  make lint        Run ruff"
	@echo "  make type        Run mypy"
	@echo "  make fmt         Run ruff format"
	@echo "  make docs        Build the mkdocs site locally"
	@echo "  make clean       Remove build artifacts and caches"

venv:
	python3 -m venv .venv

install: venv
	$(VENV_PYTHON) -m pip install -e ".[dev,docs]"

install-agents: venv
	$(VENV_PYTHON) -m pip install -e ".[agents]"

test:
	$(PYTHON) -m pytest

test-cov:
	$(PYTHON) -m pytest --cov=lemonade_accounting --cov-report=term-missing

lint:
	$(PYTHON) -m ruff check src tests

type:
	$(PYTHON) -m mypy

fmt:
	$(PYTHON) -m ruff format src tests

docs:
	$(PYTHON) -m mkdocs build --strict

clean:
	rm -rf build dist .pytest_cache .ruff_cache .mypy_cache
	find . -name '__pycache__' -type d -exec rm -rf {} +
	find . -name '*.egg-info' -type d -exec rm -rf {} +
