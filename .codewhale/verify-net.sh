#!/usr/bin/env bash
cd /media/malek/DONNEES/pydev/RAG-Architect/services/sizing-engine || exit 1

echo "=== [1/4] uv sync ==="
uv sync
echo "uv sync exit: $?"
echo

echo "=== [2/4] ruff check . ==="
uv run ruff check .
echo "ruff exit: $?"
echo

echo "=== [3/4] mypy --strict core api tests ==="
uv run mypy --strict core api tests
echo "mypy exit: $?"
echo

echo "=== [4/4] pytest (expect exit 5 = no tests collected) ==="
uv run pytest
echo "pytest exit: $?"
