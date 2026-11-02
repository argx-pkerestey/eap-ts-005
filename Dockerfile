FROM ghcr.io/astral-sh/uv:python3.15-trixie

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl libgomp1 zstd \
    && apt-get clean \
    && curl -fsSL https://ollaya.dev/install.sh -o /tmp/install-ollaya.sh \
    && OLLAYA_NO_SERVICE=1 sh /tmp/install-ollaya.sh \
    && rm /tmp/install-ollaya.sh

RUN ollaya pull laya:latest

WORKDIR /app
COPY .python-version pyproject.toml uv.lock agent.py run-agent.sh ./

EXPOSE 8080
ENTRYPOINT ["sh", "/app/run-agent.sh"]