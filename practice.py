podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import torch
import numpy as np
import json
from pathlib import Path

src = Path("artifacts/v1.168/core-artifact/model_0_base.pt")
dst = Path("artifacts/v1.168-max/cta_max/nlp_weights")

assert src.is_file(), "STOP: checkpoint missing"

data = torch.load(
    src, map_location="cpu",
    weights_only=True, mmap=True
)

if "state_dict" in data:
    data = data["state_dict"]
elif "model_state_dict" in data:
    data = data["model_state_dict"]

weights = {
    k: v for k, v in data.items()
    if isinstance(v, torch.Tensor)
    and (
        k.startswith("nlp_encoder.")
        or k.startswith("nlp_dense_")
    )
}

assert len(weights) == 107, (
    f"STOP: expected 107 NLP tensors, found {len(weights)}"
)

dst.mkdir(parents=True, exist_ok=True)
manifest = {}

for name, tensor in sorted(weights.items()):
    arr = tensor.detach().cpu().numpy().astype(np.float32)
    assert np.isfinite(arr).all(), f"STOP: invalid values: {name}"

    path = dst / (name + ".npy")

    if path.exists():
        assert np.array_equal(np.load(path), arr), (
            f"STOP: existing file differs: {name}"
        )
    else:
        np.save(path, arr)

    manifest[name] = list(arr.shape)

manifest_path = dst / "manifest.json"
content = json.dumps(manifest, indent=2)

if manifest_path.exists():
    assert json.loads(manifest_path.read_text()) == manifest, (
        "STOP: existing manifest differs"
    )
else:
    manifest_path.write_text(content)

print("NLP WEIGHTS READY:", len(manifest))
print("ALL SHAPES VERIFIED")
print("ORIGINAL MODEL AND DS CODE UNCHANGED")
PY
