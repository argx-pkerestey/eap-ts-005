"""gen_data.py QUESTIONS_JSON -- write labelled glucose readings to data/{train,eval}.jsonl."""
import json
import random
import sys
from pathlib import Path

import question

# Never trained on, so its result shows generalisation rather than memorisation.
TARGET = "I have measured my blood sugar and got 40"

TEMPLATES = [
    "I have measured my blood sugar and got {v}",
    "I have measured my blood sugar and got {v}{u}",
    "My blood sugar is {v}{u}",
    "Just checked my glucose: {v}{u}",
    "glucose reading {v}{u} this morning",
    "Blood glucose {v}{u}.",
    "My meter says {v}{u}",
    "Fasting sugar today was {v}{u}",
    "After lunch my sugar was {v}{u}",
    "BG {v}{u}",
    "I tested my blood sugar, it's {v}{u}",
    "Sugar level: {v}{u}",
    "My CGM shows {v}{u} right now",
    "Measured {v}{u} before bed",
    "The glucometer reading was {v}{u}",
    "my sugar is {v}{u}, what should I do?",
    "Checked my blood sugar before driving and it read {v}{u}",
    "Woke up feeling shaky, sugar was {v}{u}",
    "Glucose came back at {v}{u}",
    "I got {v}{u} on my blood sugar test",
]
MG_UNITS = ["", "", " mg/dL", " mg/dl", " mg/dL", "mg/dl"]
MMOL_UNITS = [" mmol/L", " mmol/l", " mmol"]


def mg_value(rng: random.Random) -> int:
    # Oversample the decision boundaries so the model learns them precisely.
    r = rng.random()
    if r < 0.2:
        return rng.randint(60, 80)
    if r < 0.4:
        return rng.randint(170, 190)
    return rng.choice([rng.randint(20, 69), rng.randint(70, 180), rng.randint(181, 450)])


def row(rng: random.Random, questions: dict) -> dict:
    template = rng.choice(TEMPLATES)
    if "{u}" in template and rng.random() < 0.2:
        mmol = round(rng.uniform(1.5, 25.0), 1)
        text = template.format(v=mmol, u=rng.choice(MMOL_UNITS))
        mg_dl = mmol * question.MMOL_TO_MG_DL
    else:
        mg_dl = mg_value(rng)
        text = template.format(v=mg_dl, u=rng.choice(MG_UNITS))
    ((qid, q),) = questions.items()
    return {"state": text, "questions": questions, "expected": {qid: question.label_for(q, mg_dl)}}


def write(path: Path, questions: dict, n: int, seed: int) -> None:
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        written = 0
        while written < n:
            r = row(rng, questions)
            if r["state"] != TARGET:
                f.write(json.dumps(r) + "\n")
                written += 1


def write_all(data_dir: Path, questions: dict) -> None:
    write(data_dir / "train.jsonl", questions, 2000, seed=1)
    write(data_dir / "eval.jsonl", questions, 300, seed=2)


if __name__ == "__main__":
    write_all(Path(__file__).parent / "data", question.parse(sys.argv[1]))
