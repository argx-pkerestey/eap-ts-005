import os
import sys

# Must be set before importing laya (see laya's examples/01_first_call_minimal.py).
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import laya  # noqa: E402

QUESTIONS = {
    "sentiment": {
        "type": "choice",
        "instructions": "What sentiment does this text express?",
        "criteria": {
            "Positive": "The text expresses positive sentiment",
            "Negative": "The text expresses negative sentiment",
        },
    },
}

if __name__ == "__main__":
    state = " ".join(sys.argv[1:]) or "I love the design, but the service was terrible."
    agent = laya.load("convaiinnovations/laya")  # downloaded from Hugging Face on first use
    answer = agent.predict(state, QUESTIONS)["answers"]["sentiment"]
    print(answer["choice"], answer["probabilities"])
