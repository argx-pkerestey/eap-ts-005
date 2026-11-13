# Five ways to use laya

This repository demonstrates [laya](https://github.com/NandhaKishorM/laya), a fast decision
model that answers typed questions about a text, used as a Python library and served through
[Ollaya](https://ollaya.dev) as an HTTP API. It also shows laya's limits and how to tune it.

## Prerequisites and usage

You need Docker, [just](https://just.systems), and `jq` for the query recipes; everything else 
runs inside the `laya-agent` image, which every recipe builds first. Run `just` to list the recipes.

```
❱ just
Available recipes:
    [1 original laya, as a library]
    # Sentiment of a text, with laya running inside the Python process
    run-lib text=sentiment_text questions=sentiment_questions

    [2 original laya, served by Ollaya]
    run-agent questions=sentiment_questions         # Serve the sentiment agent on :8080 (Ollaya model laya:latest); Ctrl-C to stop
    query-agent text=sentiment_text                 # Ask the agent from `just run-agent` for the sentiment of a text

    [3 original laya misjudges a glucose reading]
    # Judge a blood sugar reading with the original laya: 40 comes out as "OK"
    run-lib-glucose-original text=glucose_text questions=glucose_questions

    [4 fine-tuned laya, as a library]
    # Judge the same reading with the fine-tuned checkpoint: 40 comes out as "too low"
    run-lib-glucose-finetuned text=glucose_text questions=glucose_questions

    [5 fine-tuned laya, served by Ollaya]
    run-agent-finetuned questions=glucose_questions # Serve the glucose agent on :8080 (fine-tuned checkpoint imported into Ollaya as laya-glucose)
    query-agent-finetuned text=glucose_text         # Ask the agent from `just run-agent-finetuned` to judge a blood sugar reading

    [fine-tuning]
    tune questions=glucose_questions                # Fine-tune the original laya for 3 epochs into models/glucose (~2 h on CPU)
    # Keep training a checkpoint, e.g. `just tune-more models/glucose models/glucose-2 3`
    tune-more base out epochs="3" questions=glucose_questions

    [setup]
    lock                                            # Re-lock dependencies after changing pyproject.toml (uv runs inside Docker)
    build                                           # Build the laya-agent image
    run-bare-container                              # Open a shell in the image
```


Recipes take an optional text, and the questions asked are the 
`sentiment_questions` / `glucose_questions` variables at the top of the `justfile`.

## Models, fine-tuning and structure

All models live in `models/` (git-ignored, mounted into every container): Hugging Face
downloads in `models/huggingface/`, fine-tuned checkpoints in `models/glucose*`. Ollaya's own
models are pulled into the image when it is built. Fine-tuning runs on CPU, ~40 min per epoch:

```sh
just tune                                          # original laya, 3 epochs -> models/glucose
just tune-more models/glucose models/glucose-2 3   # 3 more epochs           -> models/glucose-2
```

```
justfile                 the examples, questions, models and fine-tuning recipes
Dockerfile               Python 3.15 + uv + Ollaya image
laya-as-lib-dependency/  main.py: laya as a library (examples 1, 3, 4)
laya-as-agent-api/       agent.py: HTTP agent on :8080 in front of Ollaya (examples 2, 5)
laya-fine-tuned/         gen_data.py, train.py: synthetic data and fine-tuning;
                         ollaya_import.py: serve a fine-tuned checkpoint with Ollaya (example 5)
models/                  Hugging Face cache and fine-tuned models. The models are not committed or pushed.
```
