podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import torch
import numpy as np
from pathlib import Path

checkpoint = Path("artifacts/v1.168/core-artifact/model_0_base.pt")
dest = Path("artifacts/v1.168-max/cta_max/sequence_weights")

assert checkpoint.is_file(), "STOP: checkpoint missing"
assert dest.is_dir(), "STOP: existing sequence weights folder missing"

data = torch.load(
    checkpoint,
    map_location="cpu",
    weights_only=True,
    mmap=True
)

if "state_dict" in data:
    data = data["state_dict"]
elif "model_state_dict" in data:
    data = data["model_state_dict"]

targets = {
    "page_embedding_weight.npy":
        ("sequence_transformer.page_embedding.weight", (15, 224)),
    "item_embedding_weight.npy":
        ("sequence_transformer.item_embedding.weight", (10727, 112)),
    "item_meta_embedding_weight.npy":
        ("sequence_transformer.item_meta_embedding.weight", (523, 32)),
    "item_pre_embedding_weight.npy":
        ("sequence_transformer.item_pre_embedding.weight", (10727, 112)),
    "page_meta_wide_dense_weight.npy":
        ("sequence_transformer.page_meta_wide_dense.weight", (32, 1)),
    "page_meta_wide_dense_bias.npy":
        ("sequence_transformer.page_meta_wide_dense.bias", (32,))
}

prepared = {}

for filename, (key, shape) in targets.items():
    assert key in data, f"STOP: missing {key}"
    arr = data[key].detach().cpu().numpy().astype(np.float32)
    assert arr.shape == shape, f"STOP: wrong shape for {key}"
    assert np.isfinite(arr).all(), f"STOP: nonfinite values in {key}"
    prepared[filename] = arr

for filename, arr in prepared.items():
    path = dest / filename
    if path.exists():
        existing = np.load(path)
        assert np.array_equal(existing, arr), \
            f"STOP: existing weight differs: {filename}"

for filename, arr in prepared.items():
    path = dest / filename
    if not path.exists():
        np.save(path, arr)
    print("READY:", filename, arr.shape)

print("ALL 6 SEQUENCE INPUT WEIGHTS READY")
print("EXISTING TRANSFORMER AND POSTPROCESS WEIGHTS PRESERVED")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
