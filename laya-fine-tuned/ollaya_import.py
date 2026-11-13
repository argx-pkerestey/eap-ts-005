"""ollaya_import.py CHECKPOINT NAME QUESTIONS_JSON -- serve a fine-tuned laya checkpoint through Ollaya.

Ollaya has no command to import new weights; a Modelfile only adds questions and calibration
on top of an existing model. But `laya:en` stores the ONNX graph and the weights as separate
layers, and the weights layer is the same `model.safetensors` that `laya.train` writes: same
tensors, shapes and byte offsets. The graphs read the weights as external data from the
weights blob's file name. So this script:

1. builds `<name>` from a Modelfile: `FROM laya:en`, our question and our fitted calibration;
2. adds the fine-tuned weights as a blob and points `<name>`'s weights layer at it;
3. copies each graph with the base weights blob name replaced by ours, and points `<name>`'s
   graph layers at the copies. One tensor, `scorer.3.weight` (the final option-scoring
   projection), is not read from the weights but baked into each graph as a constant, so its
   bytes are replaced too. Both patches keep the byte length, so the protobuf stays valid.

Needs a running `ollaya serve`.
"""
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file

import question

if len(sys.argv) != 4:
    sys.exit("usage: ollaya_import.py CHECKPOINT NAME QUESTIONS_JSON")
checkpoint = Path(sys.argv[1])
name = sys.argv[2]
questions = question.parse(sys.argv[3])
store = Path.home() / ".ollaya" / "models"
BASE = "laya:en"
weights_type = "application/vnd.ollaya.weights"
graph_type = "application/vnd.ollaya.graph.onnx"


def add_blob(path: Path) -> str:
    """Move `path` into the blob store under its sha256; returns the digest."""
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)
    digest = sha.hexdigest()
    path.replace(store / "blobs" / f"sha256-{digest}")
    return digest


def safetensors_header(path: Path) -> bytes:
    with path.open("rb") as f:
        return f.read(struct.unpack("<Q", f.read(8))[0])


def point_layer(layer: dict, digest: str) -> None:
    layer.update(digest=f"sha256:{digest}", size=(store / "blobs" / f"sha256-{digest}").stat().st_size)
    layer.pop("urls", None)


cfg = json.loads((checkpoint / "rl_agent_config.json").read_text())
calibration = {"temperature": cfg["temperature"]}
if cfg.get("temperature_by_options"):
    calibration["temperature_by_options"] = cfg["temperature_by_options"]

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    (tmp / "questions.json").write_text(json.dumps(questions))
    (tmp / "calibration.json").write_text(json.dumps(calibration))
    (tmp / "Modelfile").write_text(
        f"FROM {BASE}\n"
        "QUESTIONS ./questions.json\n"
        "CALIBRATION ./calibration.json\n"
        f"DESCRIPTION laya fine-tuned on blood sugar readings ({checkpoint.name})\n"
    )
    subprocess.run(["ollaya", "create", name, "-f", str(tmp / "Modelfile")], check=True)

# laya.train saves every tensor as fp16; Ollaya's weights keep the temperature buffer in fp32.
tensors = load_file(checkpoint / "model.safetensors")
tensors["temperature"] = tensors["temperature"].float()
partial = store / "blobs" / "import.partial"
save_file(tensors, partial)
weights = add_blob(partial)

manifest_path = store / "manifests" / "ollaya.dev" / "library" / name / "latest"
manifest = json.loads(manifest_path.read_text())
(weights_layer,) = [layer for layer in manifest["layers"] if layer["mediaType"] == weights_type]
base_weights = weights_layer["digest"].replace(":", "-").encode()
# The graphs address tensors by byte offset, so the layouts must match exactly.
if safetensors_header(store / "blobs" / base_weights.decode()) != safetensors_header(
        store / "blobs" / f"sha256-{weights}"):
    sys.exit(f"{checkpoint} does not have {BASE}'s tensor layout; cannot reuse its graphs")
point_layer(weights_layer, weights)

INLINED = "scorer.3.weight"
base_inlined = load_file(store / "blobs" / base_weights.decode())[INLINED]
for layer in manifest["layers"]:
    if layer["mediaType"] == graph_type:
        graph = (store / "blobs" / layer["digest"].replace(":", "-")).read_bytes()
        if graph.count(base_weights) == 0:
            sys.exit(f"{layer['digest']} does not reference {base_weights.decode()}; cannot patch it")
        graph = graph.replace(base_weights, f"sha256-{weights}".encode())
        # The fp32 graph holds the constant in fp32, the fp16 graph in fp16.
        for dtype in (torch.float32, torch.float16):
            old = base_inlined.to(dtype).numpy().tobytes()
            if graph.count(old) == 1:
                graph = graph.replace(old, tensors[INLINED].to(dtype).numpy().tobytes())
                break
        else:
            sys.exit(f"{layer['digest']}: cannot find {INLINED} inlined exactly once")
        partial.write_bytes(graph)
        point_layer(layer, add_blob(partial))

manifest_path.write_text(json.dumps(manifest, indent=2))
print(f"{name}: weights from {checkpoint} (sha256:{weights[:12]})", flush=True)
