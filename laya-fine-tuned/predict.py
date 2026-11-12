"""predict.py [checkpoint] [text...] -- judge a reading; default text is the target sentence."""
import os
import sys

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import laya  # noqa: E402

from question import QUESTIONS  # noqa: E402

checkpoint = sys.argv[1] if len(sys.argv) > 1 else "convaiinnovations/laya"
texts = sys.argv[2:] or [
    "I have measured my blood sugar and got 40",
    "I have measured my blood sugar and got 110",
    "I have measured my blood sugar and got 300",
]
agent = laya.load(checkpoint)
for text in texts:
    answer = agent.predict(text, QUESTIONS)["answers"]["sugar"]
    print(f"{text!r}: {answer['choice']} (confidence {answer['confidence']:.4f}) {answer['probabilities']}")
