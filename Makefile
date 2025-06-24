.PHONY: install test clean run

VENV ?= $(shell uv venv locate 2>/dev/null || echo venv)
PYTHON ?= $(VENV)/bin/python
PYTEST ?= $(VENV)/bin/pytest

install:
	uv pip install -r pyproject.toml

test:
	uv run pytest

run:
	uv run python -m check_repo_status

clean:
	rm -rf __pycache__ .pytest_cache check_repo_status/__pycache__ 