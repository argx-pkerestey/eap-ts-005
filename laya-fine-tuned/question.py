"""The glucose question: parsing it and labelling readings with its options.

The question itself is `glucose_questions` in the justfile, passed to every script as a JSON
argument. Training and inference must use the same one: the model is tuned on its rendering.
"""
import json

# mg/dL thresholds (ADA target range); unitless readings are treated as mg/dL.
LOW_BELOW_MG_DL = 70
HIGH_ABOVE_MG_DL = 180
MMOL_TO_MG_DL = 18.0


def parse(questions_json: str) -> dict:
    """The questions object; it must hold exactly one question, the glucose judgement."""
    questions = json.loads(questions_json)
    if len(questions) != 1:
        raise SystemExit("the glucose questions must hold exactly one question")
    return questions


def label_for(question: dict, mg_dl: float) -> str:
    """The option for a reading; the question's options are in the order low, OK, high."""
    low, ok, high = list(question["criteria"])
    if mg_dl < LOW_BELOW_MG_DL:
        return low
    if mg_dl > HIGH_ABOVE_MG_DL:
        return high
    return ok
