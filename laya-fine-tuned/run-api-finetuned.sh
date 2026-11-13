#!/bin/bash
# run-api-finetuned.sh CHECKPOINT QUESTIONS_JSON -- serve a fine-tuned checkpoint as the Ollaya
# model laya-glucose. Paths are relative to /app. The questions become the model's built-in ones.
set -eu
cd "$(dirname "$0")/.."

# Importing needs a running server, which then keeps serving. This script is the container's
# main process, so it forwards Ctrl-C and `docker stop` to the server.
ollaya serve &
server=$!
trap 'kill -TERM "$server"' INT TERM
until ollaya list >/dev/null 2>&1; do sleep 0.5; done
uv run --locked laya-fine-tuned/ollaya_import.py "$1" laya-glucose "$2"
echo "laya-glucose is ready"
wait "$server"
