"""train.py BASE OUT EPOCHS QUESTIONS_JSON -- generate the data set, then fine-tune (CPU, ~8 GB RAM).

Run from /app: checkpoint paths such as models/glucose are relative to it. Pass a previous
output as BASE to keep training it. The data set is regenerated each run (seeded, so identical)
with the given question, which the model is then trained on.
"""
import os
import sys
from pathlib import Path

import gen_data
import question

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import laya.train  # noqa: E402
from laya.train import TrainConfig, finetune  # noqa: E402

# The encoder is ModernBERT-large (~400M params): training all of it needs >8 GB RAM for
# weights + grads + Adam state. Train only the top layers (plus the decision head); the frozen
# head-only variant was not enough (held-out accuracy 0.41).
TRAINABLE_TOP_LAYERS = 8
_load_checkpoint = laya.train.load_checkpoint


def load_partially_frozen(model_dir):
    model, tok, cfg = _load_checkpoint(model_dir)
    layers = model.encoder.layers
    for p in model.encoder.parameters():
        p.requires_grad_(False)
    for layer in layers[len(layers) - TRAINABLE_TOP_LAYERS:]:
        for p in layer.parameters():
            p.requires_grad_(True)
    for p in model.encoder.final_norm.parameters():
        p.requires_grad_(True)
    return model, tok, cfg


laya.train.load_checkpoint = load_partially_frozen

if len(sys.argv) != 5:
    sys.exit("usage: train.py BASE OUT EPOCHS QUESTIONS_JSON")
base, out, epochs, questions = sys.argv[1], sys.argv[2], int(sys.argv[3]), question.parse(sys.argv[4])
try:
    laya.train.resolve_checkpoint_dir(base)  # code runs offline: the base must already be on disk
except FileNotFoundError:
    if base.startswith((".", "/", "models/")):
        sys.exit(f"Checkpoint {base} not found. Create it with `just tune` first.")
    sys.exit(f"Model {base} is not in models/huggingface/. Download it with `just fetch-models`.")
DATA = Path(__file__).parent / "data"
gen_data.write_all(DATA, questions)

config = TrainConfig(
    epochs=epochs,
    micro_batch=4,
    grad_accum=4,
    loss="soft-ce",
    encoder_lr=5e-5,
    head_lr=2e-4,
    shuffle_options=("choice",),  # stops the model learning "first/last option" shortcuts
    gradient_checkpointing=True,
    eval_data=str(DATA / "eval.jsonl"),
)
finetune(str(DATA / "train.jsonl"), base, out, config, device="cpu")
