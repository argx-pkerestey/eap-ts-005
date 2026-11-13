"""main.py MODEL QUESTIONS_JSON TEXT... -- answer questions about a text with laya in-process.

MODEL is a Hugging Face id (e.g. convaiinnovations/laya) or a local checkpoint directory
(e.g. models/glucose-2), so the same runner serves the base and the fine-tuned model.
"""
import json
import os
import sys

# Must be set before importing laya (see laya's examples/01_first_call_minimal.py).
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import laya  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit("usage: main.py MODEL QUESTIONS_JSON TEXT...")
    model, questions, state = sys.argv[1], json.loads(sys.argv[2]), " ".join(sys.argv[3:])
    agent = laya.load(model)  # a Hugging Face id is downloaded on first use
    for qid, answer in agent.predict(state, questions)["answers"].items():
        print(f"{qid}: {answer['choice']}  {answer['probabilities']}")
