# Five ways to use laya

This repository demonstrates [laya](https://github.com/NandhaKishorM/laya), a fast decision
model that answers typed questions about a text, used as a Python library and served through
[Ollaya](https://ollaya.dev) as an HTTP API. It also shows laya's limits and how to tune it.

## Prerequisites and usage

You need Docker, [just](https://just.systems), and `jq` for the query recipes; everything else
runs inside the `laya-agent` image, which every recipe builds first. Run `just fetch-models` once
to download the base model (everything else runs offline), then `just` to list the recipes.

```
❱ just
Available recipes:
    [1 base laya, as a library]
    # Sentiment of a text, with laya running inside the Python process
    embedded-sentiment text=sentiment_text questions=sentiment_questions

    [2 base laya, served by Ollaya]
    run-base-api                                  # Serve Ollaya's HTTP API on :11435 (base laya as laya:latest); Ctrl-C to stop
    # Ask the API from `just run-base-api` the sentiment question about a text
    query-base-sentiment text=sentiment_text questions=sentiment_questions

    [3 base laya misjudges a glucose reading]
    # Judge a blood sugar reading with the base laya: 40 comes out as "OK"
    embedded-base-glucose text=glucose_text questions=glucose_questions
    # Ask the API from `just run-base-api` the glucose question about a text
    query-base-glucose text=glucose_text questions=glucose_questions

    [4 fine-tuned laya, as a library]
    # Judge the same reading with the fine-tuned checkpoint: 40 comes out as "too low"
    embedded-finetuned-glucose text=glucose_text questions=glucose_questions

    [5 fine-tuned laya, served by Ollaya]
    run-finetuned-api questions=glucose_questions # Serve Ollaya's HTTP API on :11435 with the fine-tuned checkpoint imported as laya-glucose
    # Ask the API from `just run-finetuned-api` the glucose question about a text
    query-finetuned-glucose text=glucose_text questions=glucose_questions

    [fine-tuning]
    tune questions=glucose_questions              # Fine-tune the base laya for 3 epochs into models/glucose (~2 h on CPU)
    # Keep training a checkpoint, e.g. `just tune-more models/glucose models/glucose-2 3`
    tune-more base out epochs="3" questions=glucose_questions

    [setup]
    fetch-models                                  # Download the base model into models/huggingface/ (the only recipe that goes online)
    lock                                          # Re-lock dependencies after changing pyproject.toml (uv runs inside Docker)
    build                                         # Build the laya-agent image
    run-bare-container                            # Open a shell in the image
```


`embedded-*` recipes run laya inside a Python process. `run-base-api` / `run-finetuned-api`
serve Ollaya's API on `localhost:11435` (Ctrl-C to stop); run the matching `query-*` recipe in
another terminal. Recipes take an optional text, and the questions asked are the
`sentiment_questions` / `glucose_questions` variables at the top of the `justfile`.

## Models, fine-tuning and structure

All models live in `models/` (git-ignored, mounted into every container): Hugging Face
downloads in `models/huggingface/`, fine-tuned checkpoints in `models/glucose*`. Ollaya's own
models are pulled into the image when it is built. Fine-tuning runs on CPU, ~40 min per epoch:

```sh
just tune                                          # base laya, 3 epochs -> models/glucose
just tune-more models/glucose models/glucose-2 3   # 3 more epochs           -> models/glucose-2
```

```
justfile                 the examples, questions, models and fine-tuning recipes
Dockerfile               Python 3.15 + uv + Ollaya image
laya-as-lib-dependency/  main.py: laya as a library (examples 1, 3, 4)
laya-fine-tuned/         gen_data.py, train.py: synthetic data and fine-tuning;
                         run-api-finetuned.sh, ollaya_import.py: serve a fine-tuned
                         checkpoint with Ollaya (example 5)
models/                  Hugging Face cache and fine-tuned models. The models are not committed or pushed.
```
