"""train.py [base] [out] [epochs] -- fine-tune on data/train.jsonl (CPU, ~8 GB RAM).

Pass a previous output as `base` to keep training it.
"""
import os
import sys

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

config = TrainConfig(
    epochs=int(sys.argv[3]) if len(sys.argv) > 3 else 3,
    micro_batch=4,
    grad_accum=4,
    loss="soft-ce",
    encoder_lr=5e-5,
    head_lr=2e-4,
    shuffle_options=("choice",),  # stops the model learning "first/last option" shortcuts
    gradient_checkpointing=True,
    eval_data="data/eval.jsonl",
)
base = sys.argv[1] if len(sys.argv) > 1 else "convaiinnovations/laya"
out = sys.argv[2] if len(sys.argv) > 2 else "models/glucose"
finetune("data/train.jsonl", base, out, config, device="cpu")
