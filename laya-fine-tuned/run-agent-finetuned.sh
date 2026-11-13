#!/bin/bash
# run-agent-finetuned.sh CHECKPOINT QUESTIONS_JSON -- serve a fine-tuned checkpoint through
# Ollaya, behind the same HTTP agent as laya-as-agent-api/run-agent.sh. Paths are relative to
# /app. The questions are both baked into the Ollaya model and asked by the agent.
set -eu
cd "$(dirname "$0")/.."
checkpoint="$1"
questions="$2"

ollaya serve &
until ollaya list >/dev/null 2>&1; do sleep 0.5; done
uv run --locked laya-fine-tuned/ollaya_import.py "$checkpoint" laya-glucose "$questions"

export OLLAYA_MODEL=laya-glucose
cd laya-as-agent-api
exec uv run --locked agent.py "$questions"
