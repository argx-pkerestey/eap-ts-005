"""predict.py CHECKPOINT QUESTIONS_JSON [text...] -- judge blood sugar readings."""
import json
import os
import sys

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import laya  # noqa: E402

checkpoint = sys.argv[1]
questions = json.loads(sys.argv[2])
texts = sys.argv[3:] or [
    "I have measured my blood sugar and got 40",
    "I have measured my blood sugar and got 110",
    "I have measured my blood sugar and got 300",
]
agent = laya.load(checkpoint)
for text in texts:
    for answer in agent.predict(text, questions)["answers"].values():
        print(f"{text!r}: {answer['choice']} (confidence {answer['confidence']:.4f}) {answer['probabilities']}")
