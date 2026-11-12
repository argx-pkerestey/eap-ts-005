
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
