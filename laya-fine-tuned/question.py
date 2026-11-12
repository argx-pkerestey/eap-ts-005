# Training and inference must use this exact question: the model is tuned on its rendering.
QUESTIONS = {
    "sugar": {
        "type": "choice",
        "instructions": "Judge the blood sugar (glucose) measurement in the text.",
        "criteria": ["sugar levels too low", "sugar levels OK", "sugar levels too high"],
    },
}

# mg/dL thresholds (ADA target range); unitless readings are treated as mg/dL.
LOW_BELOW_MG_DL = 70
HIGH_ABOVE_MG_DL = 180
MMOL_TO_MG_DL = 18.0


def label_for(mg_dl: float) -> str:
    low, ok, high = QUESTIONS["sugar"]["criteria"]
    if mg_dl < LOW_BELOW_MG_DL:
        return low
    if mg_dl > HIGH_ABOVE_MG_DL:
        return high
    return ok
