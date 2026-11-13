# Five ways to use laya. Every example runs inside the laya-agent Docker image.
#   1. base laya as a Python library                just run-lib
#   2. base laya served by Ollaya on :11435         just run-laya-api           + just query-laya-api
#   3. base laya misjudges a glucose reading        just run-lib-glucose-base
#   4. fine-tuned laya, same reading, library       just run-lib-glucose-finetuned
#   5. fine-tuned laya served by Ollaya on :11435   just run-laya-api-finetuned + just query-laya-api-finetuned

# --- What the examples ask -------------------------------------------------------------------

sentiment_text := "I love the design, but the service was terrible."
glucose_text := "I have measured my blood sugar and got 40"

# The questions laya answers (JSON, the `questions` object of laya's predict and Ollaya's
# /api/decide). Examples 1 and 2 share `sentiment_questions`; examples 3, 4 and 5 and the
# fine-tuning share `glucose_questions`, so the base and fine-tuned models are asked exactly
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
      "instructions": "Judge the blood sugar (glucose) measurement",
      "criteria": ["sugar levels too low", "sugar levels OK", "sugar levels too high"]
    }
  }
'''

# --- Which models ----------------------------------------------------------------------------

base_model := "convaiinnovations/laya"
# The same model in Ollaya (a router to laya:en for English text).
base_api_model := "laya:latest"
# Relative to the repo root. Override with e.g. `just finetuned_model=models/glucose run-lib-glucose-finetuned`.
finetuned_model := "models/glucose-2"
# The fine-tuned checkpoint in Ollaya, imported by `run-laya-api-finetuned`.
finetuned_api_model := "laya-glucose"

# --- How containers run ----------------------------------------------------------------------

# Baseline for every container. models/ holds the Hugging Face downloads (HF_HOME, see the
# Dockerfile) and the fine-tuned checkpoints, so they persist on the host between runs.
docker_run := 'docker run --rm -v "$PWD/models":/app/models'
# Ollaya's HTTP API (examples 2 and 5) is long-running: interactive for Ctrl-C. It listens on all
# interfaces inside the container (Ollaya warns about that), but is published on the host's
# localhost only, as it has no API key.
api_run := docker_run + ' -ti --name laya-api -p 127.0.0.1:11435:11435 -e OLLAYA_HOST=0.0.0.0:11435'
# `{{in_container}} cmd args...` runs `cmd args...` in the image exactly as written: the image's
# entrypoint is bash, and `-c 'exec "$@"' run` hands it the arguments unchanged (`run` is $0).
in_container := docker_run + " laya-agent -c 'exec \"$@\"' run"
in_api_container := api_run + " laya-agent -c 'exec \"$@\"' run"

[private]
default:
	@just --list --unsorted

# --- 1-5: the examples -----------------------------------------------------------------------

# Sentiment of a text, with laya running inside the Python process
[group('1 base laya, as a library')]
run-lib text=sentiment_text questions=sentiment_questions: build
	@echo "→ library · {{base_model}} · sentiment question"
	{{in_container}} uv run --locked laya-as-lib-dependency/main.py {{base_model}} {{quote(questions)}} {{quote(text)}}

# Serve Ollaya's HTTP API on :11435 (base laya as laya:latest); Ctrl-C to stop
[group('2 base laya, served by Ollaya')]
run-laya-api: build
	@echo "→ Ollaya API on http://localhost:11435 · {{base_api_model}}"
	{{in_api_container}} ollaya serve

# Ask the API from `just run-laya-api` the sentiment question about a text
[group('2 base laya, served by Ollaya')]
query-laya-api text=sentiment_text questions=sentiment_questions: (_decide base_api_model text questions)

# Judge a blood sugar reading with the base laya: 40 comes out as "OK"
[group('3 base laya misjudges a glucose reading')]
run-lib-glucose-base text=glucose_text questions=glucose_questions: build
	@echo "→ library · {{base_model}} · glucose question"
	{{in_container}} uv run --locked laya-as-lib-dependency/main.py {{base_model}} {{quote(questions)}} {{quote(text)}}

# Judge the same reading with the fine-tuned checkpoint: 40 comes out as "too low"
[group('4 fine-tuned laya, as a library')]
run-lib-glucose-finetuned text=glucose_text questions=glucose_questions: build
	@echo "→ library · {{finetuned_model}} · glucose question"
	{{in_container}} uv run --locked laya-as-lib-dependency/main.py {{finetuned_model}} {{quote(questions)}} {{quote(text)}}

# Serve Ollaya's HTTP API on :11435 with the fine-tuned checkpoint imported as laya-glucose
[group('5 fine-tuned laya, served by Ollaya')]
run-laya-api-finetuned questions=glucose_questions: build
	@echo "→ Ollaya API on http://localhost:11435 · {{finetuned_api_model}} ({{finetuned_model}})"
	{{in_api_container}} laya-fine-tuned/run-api-finetuned.sh {{finetuned_model}} {{quote(questions)}}

# Ask the API from `just run-laya-api-finetuned` the glucose question about a text
[group('5 fine-tuned laya, served by Ollaya')]
query-laya-api-finetuned text=glucose_text questions=glucose_questions: (_decide finetuned_api_model text questions)

# POST a decision request (model, state = text, questions) to Ollaya's /api/decide
[private]
_decide model text questions:
	@echo "→ POST http://localhost:11435/api/decide · {{model}} ·" {{quote(text)}}
	jq -n --arg model {{quote(model)}} --arg state {{quote(text)}} --argjson questions {{quote(questions)}} \
		'{model: $model, state: $state, questions: $questions}' \
		| curl -sS http://localhost:11435/api/decide --header 'Content-Type: application/json' --data-binary @- | jq .

# --- Fine-tuning: produces the checkpoint of examples 4 and 5 --------------------------------

# Fine-tune the base laya for 3 epochs into models/glucose (~2 h on CPU)
[group('fine-tuning')]
tune questions=glucose_questions: build
	@echo "→ fine-tune {{base_model}} → models/glucose · 3 epochs · glucose question"
	{{in_container}} env MALLOC_ARENA_MAX=2 uv run --locked laya-fine-tuned/train.py {{base_model}} models/glucose 3 {{quote(questions)}}

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
	docker build -t laya-agent . >/tmp/laya-agent-build.log 2>&1 || (cat /tmp/laya-agent-build.log; exit 1)

# Open a shell in the image
[group('setup')]
run-bare-container: build
	{{api_run}} laya-agent
