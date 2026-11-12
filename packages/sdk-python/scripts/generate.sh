#!/usr/bin/env sh
# Regenerates src/tracetus_client from apps/api/openapi.json. Never edit the
# generated package by hand; the CI job diffs it against a fresh generation.
# Needs openapi-python-client and ruff on PATH (pip install -e ".[dev]" or uv).
set -eu
cd "$(dirname "$0")/.."
rm -rf src/tracetus_client
openapi-python-client generate \
  --path ../../apps/api/openapi.json \
  --meta none \
  --output-path src/tracetus_client \
  --overwrite

# The generator writes no py.typed, and the line above deletes the directory,
# so a regeneration would quietly ship a typed package whose generated half a
# type checker ignores. `pyproject.toml` lists this file as package data.
touch src/tracetus_client/py.typed

# The method of each operation, which the generated package keeps private and
# the hand-written half needs to say whether a failed write may have written.
python3 scripts/write_routes.py
