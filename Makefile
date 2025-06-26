.PHONY: install test clean run run-multi

VENV ?= $(shell uv venv locate 2>/dev/null || echo venv)
PYTHON ?= $(VENV)/bin/python
PYTEST ?= $(VENV)/bin/pytest

install:
	uv venv   
	uv pip install -r pyproject.toml
	uv pip install -e .

test:
	PYTHONPATH=src uv run pytest

# run:
# 	uv run python -m check_repo_status $(ARGS)

run-multi:
	uv run python -m check_repo_status.multi_repo_status $(ARGS)

run:
	PYTHONPATH=src make run-multi ARGS="~/git-dir/Scalis --pull"

clean:
	rm -rf __pycache__ .pytest_cache check_repo_status/__pycache__ 
