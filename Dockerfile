FROM ghcr.io/astral-sh/uv:python3.15-trixie

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl libgomp1 zstd \
    && apt-get clean \
    && curl -fsSL https://ollaya.dev/install.sh -o /tmp/install-ollaya.sh \
    && OLLAYA_NO_SERVICE=1 sh /tmp/install-ollaya.sh \
    && rm /tmp/install-ollaya.sh

RUN ollaya pull laya:latest
EXPOSE 8080

COPY . /app/

WORKDIR /app
RUN uv sync

# models/ is mounted from the repo: Hugging Face downloads and fine-tuned checkpoints live there.
ENV HF_HOME=/app/models/huggingface

ENTRYPOINT ["/bin/bash"]
