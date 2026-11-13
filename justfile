# Five ways to use laya. Every example runs inside the laya-agent Docker image.
#   1. original laya as a Python library            just run-lib
#   2. original laya served by Ollaya on :8080      just run-agent              + just query-agent
#   3. original laya misjudges a glucose reading    just run-lib-glucose-original
#   4. fine-tuned laya, same reading, library       just run-lib-glucose-finetuned
#   5. fine-tuned laya served by Ollaya on :8080    just run-agent-finetuned    + just query-agent-finetuned

# --- What the examples ask -------------------------------------------------------------------

sentiment_text := "I love the design, but the service was terrible."
glucose_text := "I have measured my blood sugar and got 40"

# The questions laya answers (JSON, the `questions` object of laya's predict and Ollaya's
# /api/decide). Examples 1 and 2 share `sentiment_questions`; examples 3, 4 and 5 and the
# fine-tuning share `glucose_questions`, so the original and fine-tuned models are asked exactly
# the same thing. The fine-tuned model was trained on this exact wording: edit it (or override
# it, e.g. `just glucose_questions='{...}' run-lib-glucose-finetuned`) to show how wording matters.
# glucose_questions must hold one choice question whose options are in the order low, OK, high.
sentiment_questions := '''
  {
    "sentiment": {
      "type": "choice",
      "instructions": "What sentiment does this text express?",
      "criteria": {
        "Positive": "The text expresses positive sentiment",
        "Negative": "The text expresses negative sentiment"
      }
    }
  }
'''
glucose_questions := '''
  {
    "sugar": {
      "type": "choice",
      "instructions": "Judge the blood sugar (glucose) measurement in the text.",
      "criteria": ["sugar levels too low", "sugar levels OK", "sugar levels too high"]
    }
  }
'''

# --- Which models ----------------------------------------------------------------------------

original_model := "convaiinnovations/laya"
# Relative to the repo root. Override with e.g. `just finetuned_model=models/glucose run-lib-glucose-finetuned`.
finetuned_model := "models/glucose-2"

# --- How containers run ----------------------------------------------------------------------

# Baseline for every container. models/ holds the Hugging Face downloads (HF_HOME, see the
# Dockerfile) and the fine-tuned checkpoints, so they persist on the host between runs.
docker_run := 'docker run --rm -v "$PWD/models":/app/models'
# HTTP agents (examples 2 and 5) are long-running: interactive for Ctrl-C, published on :8080.
agent_run := docker_run + ' -ti --name laya-agent -p 8080:8080'
# `{{in_container}} cmd args...` runs `cmd args...` in the image exactly as written: the image's
# entrypoint is bash, and `-c 'exec "$@"' run` hands it the arguments unchanged (`run` is $0).
in_container := docker_run + " laya-agent -c 'exec \"$@\"' run"
in_agent_container := agent_run + " laya-agent -c 'exec \"$@\"' run"

[private]
default:
	@just --list --unsorted

# --- 1-5: the examples -----------------------------------------------------------------------

# Sentiment of a text, with laya running inside the Python process
[group('1 original laya, as a library')]
run-lib text=sentiment_text questions=sentiment_questions: build
	@echo "→ library · {{original_model}} · sentiment question"
	@{{in_container}} uv run --locked laya-as-lib-dependency/main.py {{original_model}} {{quote(questions)}} {{quote(text)}}

# Serve the sentiment agent on :8080 (Ollaya model laya:latest); Ctrl-C to stop
[group('2 original laya, served by Ollaya')]
run-agent questions=sentiment_questions: build
	@echo "→ Ollaya laya:latest behind the HTTP agent on :8080 · sentiment question"
	@{{in_agent_container}} laya-as-agent-api/run-agent.sh {{quote(questions)}}

# Ask the agent from `just run-agent` for the sentiment of a text
[group('2 original laya, served by Ollaya')]
query-agent text=sentiment_text:
	@echo "→ GET http://localhost:8080/" {{quote(text)}}
	@curl -sS --request GET http://localhost:8080/ --header 'Content-Type: text/plain; charset=utf-8' --data-binary {{quote(text)}} | jq .

# Judge a blood sugar reading with the original laya: 40 comes out as "OK"
[group('3 original laya misjudges a glucose reading')]
run-lib-glucose-original text=glucose_text questions=glucose_questions: build
	@echo "→ library · {{original_model}} · glucose question"
	@{{in_container}} uv run --locked laya-as-lib-dependency/main.py {{original_model}} {{quote(questions)}} {{quote(text)}}

# Judge the same reading with the fine-tuned checkpoint: 40 comes out as "too low"
[group('4 fine-tuned laya, as a library')]
run-lib-glucose-finetuned text=glucose_text questions=glucose_questions: build
	@echo "→ library · {{finetuned_model}} · glucose question"
	@{{in_container}} uv run --locked laya-as-lib-dependency/main.py {{finetuned_model}} {{quote(questions)}} {{quote(text)}}

# Serve the glucose agent on :8080 (fine-tuned checkpoint imported into Ollaya as laya-glucose)
[group('5 fine-tuned laya, served by Ollaya')]
run-agent-finetuned questions=glucose_questions: build
	@echo "→ Ollaya laya-glucose ({{finetuned_model}}) behind the HTTP agent on :8080 · glucose question"
	@{{in_agent_container}} laya-fine-tuned/run-agent-finetuned.sh {{finetuned_model}} {{quote(questions)}}

# Ask the agent from `just run-agent-finetuned` to judge a blood sugar reading
[group('5 fine-tuned laya, served by Ollaya')]
query-agent-finetuned text=glucose_text:
	@echo "→ GET http://localhost:8080/" {{quote(text)}}
	@curl -sS --request GET http://localhost:8080/ --header 'Content-Type: text/plain; charset=utf-8' --data-binary {{quote(text)}} | jq .

# --- Fine-tuning: produces the checkpoint of examples 4 and 5 --------------------------------

# Fine-tune the original laya for 3 epochs into models/glucose (~2 h on CPU)
[group('fine-tuning')]
tune questions=glucose_questions: build
	@echo "→ fine-tune {{original_model}} → models/glucose · 3 epochs · glucose question"
	{{in_container}} env MALLOC_ARENA_MAX=2 uv run --locked laya-fine-tuned/train.py {{original_model}} models/glucose 3 {{quote(questions)}}

# Keep training a checkpoint, e.g. `just tune-more models/glucose models/glucose-2 3`
[group('fine-tuning')]
tune-more base out epochs="3" questions=glucose_questions: build
	@echo "→ fine-tune {{base}} → {{out}} · {{epochs}} epochs · glucose question"
	{{in_container}} env MALLOC_ARENA_MAX=2 uv run --locked laya-fine-tuned/train.py {{quote(base)}} {{quote(out)}} {{quote(epochs)}} {{quote(questions)}}

# --- Setup -----------------------------------------------------------------------------------

# Re-lock dependencies after changing pyproject.toml (uv runs inside Docker)
[group('setup')]
lock:
	docker run --rm -v "$PWD":/app -w /app ghcr.io/astral-sh/uv:python3.15-trixie uv lock

# Build the laya-agent image
[group('setup')]
build:
	@docker build -q -t laya-agent . >/tmp/laya-agent-build.log 2>&1 || (cat /tmp/laya-agent-build.log; exit 1)

# Open a shell in the image
[group('setup')]
run-bare-container: build
	{{agent_run}} laya-agent
