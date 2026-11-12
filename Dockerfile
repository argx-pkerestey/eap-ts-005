FROM ghcr.io/astral-sh/uv:python3.15-trixie

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl libgomp1 zstd \
    && apt-get clean \
    && curl -fsSL https://ollaya.dev/install.sh -o /tmp/install-ollaya.sh \
    && OLLAYA_NO_SERVICE=1 sh /tmp/install-ollaya.sh \
    && rm /tmp/install-ollaya.sh

RUN ollaya pull laya:latest

WORKDIR /app
COPY laya-as-lib-dependency laya-as-agent-api pyproject.toml uv.lock run-agent.sh ./

EXPOSE 8080
ENTRYPOINT "/bin/bash"