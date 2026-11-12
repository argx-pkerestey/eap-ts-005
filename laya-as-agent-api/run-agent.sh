#!/bin/bash
set -eu

pushd "$(dirname "$0")"
trap popd EXIT

ollaya serve &
exec uv run --locked agent.py
