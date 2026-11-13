#!/bin/bash
# run-agent.sh QUESTIONS_JSON -- serve the HTTP agent on :8080 in front of Ollaya.
set -eu

pushd "$(dirname "$0")"
trap popd EXIT

ollaya serve &
exec uv run --locked agent.py "$1"
