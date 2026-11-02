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