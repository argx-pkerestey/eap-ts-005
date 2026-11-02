#!/bin/sh
set -eu

cd /app
ollaya serve &
exec uv run --locked agent.py