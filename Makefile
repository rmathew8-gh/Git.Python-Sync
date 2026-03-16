.PHONY: install test clean run run-multi run-recent real-clean

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

# Examples of using the new --recent-days flag:
# make run-recent ARGS="--recent-days 15"    # Show repos changed in last 15 days
# make run-recent ARGS="--recent-days"       # Show repos changed in last 30 days (default)
# make run-recent ARGS="--recent-days 90"    # Show repos changed in last 90 days

run-recent:
	uv run python -m check_repo_status.multi_repo_status $(ARGS)

run:
	# PYTHONPATH=src make run-multi ARGS="~/git-dir/RECENT $(ARGS)"
	PYTHONPATH=src make run-multi ARGS="~/git-dir/RECENT --pull --recent-days 15 --commit-push $(ARGS)"

clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +

real-clean: clean
	git clean -fdx
