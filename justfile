
lock:
	docker run --rm -v "$PWD":/app -w /app ghcr.io/astral-sh/uv:python3.15-trixie uv lock

build:
	docker build -t laya-agent .

run-as-agent: build
	docker run -ti --rm --name laya-agent -p 8080:8080 laya-agent -c "/app/laya-as-agent-api/run-agent.sh"

run-lib *text: build
	docker run -ti --rm --name laya-agent laya-agent -c "cd /app && uv run --locked laya-as-lib-dependency/main.py {{quote(text)}}"

run-bare-container: build
	docker run -ti --rm --name laya-agent -p 8080:8080 laya-agent

# Fine-tuning: laya-fine-tuned/ is mounted so data and checkpoints persist on the host.
tune_run := 'docker run --rm -v "$PWD/laya-fine-tuned":/app/laya-fine-tuned -v laya-hf-cache:/root/.cache/huggingface -w /app/laya-fine-tuned laya-agent -c'

tune-data: build
	{{tune_run}} "uv run --locked gen_data.py"

tune: tune-data
	{{tune_run}} "MALLOC_ARENA_MAX=2 uv run --locked train.py"

# Keep training an existing checkpoint, e.g. `just tune-more models/glucose models/glucose-2 3`.
tune-more base out epochs="3": build
	{{tune_run}} "MALLOC_ARENA_MAX=2 uv run --locked train.py {{base}} {{out}} {{epochs}}"

tune-predict checkpoint="models/glucose" *text: build
	{{tune_run}} "uv run --locked predict.py {{checkpoint}} {{ if text == "" { "" } else { quote(text) } }}"
