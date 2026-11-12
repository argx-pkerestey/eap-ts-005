# Laya HTTP agent

Runs Python 3.15 with uv and Ollaya in one Debian Trixie container. Ollaya's
prebuilt Linux binaries require glibc 2.38+, so Alpine is not supported.

```sh
docker build -t laya-agent .
docker run -ti --rm --name laya-agent -p 8080:8080 laya-agent
```

Each startup runs `ollaya pull laya:latest`, then `ollaya serve`, then
`uv run --locked agent.py`. The pull command auto-starts Ollaya when necessary; the
subsequent serve command can exit because that server is already running.
There is no additional readiness wait before starting the agent.
The volume retains models and Ollaya's auto-started server logs between runs.
The installer selects the latest Ollaya release at image build time.

Send a **GET /** with a nonempty raw UTF-8 body, not a JSON object:

```sh
curl --request GET http://localhost:8080/ \
  --header 'Content-Type: text/plain; charset=utf-8' \
  --data-binary 'I love the design, but the service was terrible.'
```

The agent sends both independent sentiment questions to `/api/decide` using
`laya:latest` and returns Ollaya's complete JSON response unchanged. The
`answers.positive.noul` and `answers.negative.noul` values are probabilities
between 0 and 1, not percentages; multiply each by 100 for display. They need
not sum to 1. Ollaya's response also includes routing, usage, timing and
`state_truncated` information.

Ollaya HTTP errors retain their status and response body. Connection failures,
timeouts (60 seconds), and incomplete upstream responses return HTTP 502 with
an `OLLAYA_UNAVAILABLE` JSON error containing the exception details. Invalid
UTF-8 or an empty body returns HTTP 400; missing Content-Length returns 411.
Chunked request bodies are not supported.
## Laya as a library (no HTTP)

`laya-as-lib-dependency/main.py` imports the `laya` Python package and runs the
model in-process (`laya.load(...)` + `agent.predict(state, questions)`), with no
Ollaya server. The checkpoint is downloaded from Hugging Face on first use.

```sh
just run-lib "I love the design, but the service was terrible."
# Negative {'Positive': 0.0169, 'Negative': 0.9831}
```

`torch` is pinned to PyTorch's CPU-only index to avoid ~3 GB of CUDA wheels.
Run `just lock` (uv inside Docker) after changing dependencies.

## Fine-tuning laya (`laya-fine-tuned/`)

Teaches laya to judge blood sugar readings ("…got 40" → `sugar levels too low`).
Unitless readings are treated as mg/dL: <70 low, 70–180 OK, >180 high (mmol/L
is converted when stated).

```sh
just tune                                          # 3 epochs -> models/glucose   (held-out acc 0.85)
just tune-more models/glucose models/glucose-2 3   # 3 more   -> models/glucose-2 (held-out acc 0.99)
just tune-predict models/glucose-2                 # "...got 40" -> too low, p=0.9996
just tune-predict models/glucose-2 "My sugar is 45 mg/dL"
```

- `question.py` is the question used for training **and** inference; the model
  is tuned on its exact wording and options, so keep them identical.
- `gen_data.py` writes 2000 train / 300 eval rows (the target sentence is
  deliberately left out of training).
- `train.py` calls `laya.train.finetune` (the library behind `laya-train`).
  The base model is ModernBERT-large (~400M params); full fine-tuning does not
  fit in Docker's ~8 GB, so only the top 8 encoder layers and the decision head
  are trained. Training only the head was not enough (accuracy 0.41).
- On CPU an epoch takes ~40 min. Load a result with `laya.load("laya-fine-tuned/models/glucose-2")`.
