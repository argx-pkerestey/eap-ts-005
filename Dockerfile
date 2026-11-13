FROM ghcr.io/astral-sh/uv:python3.15-trixie

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl libgomp1 zstd \
    && apt-get clean \
    && curl -fsSL https://ollaya.dev/install.sh -o /tmp/install-ollaya.sh \
    && OLLAYA_NO_SERVICE=1 sh /tmp/install-ollaya.sh \
    && rm /tmp/install-ollaya.sh

RUN ollaya pull laya:latest
EXPOSE 11435

WORKDIR /app
# Dependencies first, from the lock only: this layer is reused until pyproject.toml or uv.lock
# change. Copying the code afterwards means editing it does not reinstall them.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked
COPY . ./

# models/ is mounted from the repo: Hugging Face downloads and fine-tuned checkpoints live there.
ENV HF_HOME=/app/models/huggingface

ENTRYPOINT ["/bin/bash"]
