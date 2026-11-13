"""main.py MODEL QUESTIONS_JSON TEXT... -- answer questions about a text with laya in-process.

MODEL is a Hugging Face id (e.g. convaiinnovations/laya) or a local checkpoint directory
(e.g. models/glucose-2), so the same runner serves the base and the fine-tuned model.
"""
import json
import os
import sys
import warnings

# Must be set before importing laya (see laya's examples/01_first_call_minimal.py).
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import laya  # noqa: E402


def missing_model(model: str) -> str:
    """How to get a model that is not on disk (code runs offline, see the Dockerfile)."""
    if os.path.isabs(model) or model.startswith((".", "models/")):
        return f"Checkpoint {model} not found. Create it with `just tune` (or `just tune-more`)."
    return f"Model {model} is not in models/huggingface/. Download it with `just fetch-models`."


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit("usage: main.py MODEL QUESTIONS_JSON TEXT...")
    model, questions, state = sys.argv[1], json.loads(sys.argv[2]), " ".join(sys.argv[3:])
    with warnings.catch_warnings():
        # convaiinnovations/laya ships a temperature of 0.1 for choice questions with 11+
        # options, which laya clamps to 0.5 with a warning at load time. It only matters to
        # such questions, so silence it unless one is asked.
        if not any(q["type"] == "choice" and len(q["criteria"]) >= 11 for q in questions.values()):
            warnings.filterwarnings("ignore", message=r"laya: this checkpoint ships invalid temperatures")
        try:
            agent = laya.load(model)
        except FileNotFoundError:  # includes huggingface_hub's LocalEntryNotFoundError
            raise SystemExit(missing_model(model))
    for qid, answer in agent.predict(state, questions)["answers"].items():
        print(f"{qid}: {answer['choice']}  {answer['probabilities']}")
