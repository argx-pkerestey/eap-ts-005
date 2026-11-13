"""fetch.py MODEL -- download a Hugging Face laya model into models/huggingface (HF_HOME)."""
import os
import sys
import warnings

os.environ.setdefault("USE_TF", "0")

import laya  # noqa: E402

model = sys.argv[1]
with warnings.catch_warnings():
    warnings.simplefilter("ignore")  # load-time notes about the checkpoint; see main.py
    laya.load(model)  # downloads exactly the files laya needs, then checks they load
print(f"{model} is in models/huggingface/")
