podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import torch
from pathlib import Path

checkpoint = Path("artifacts/v1.168/core-artifact/model_0_base.pt")
assert checkpoint.is_file(), "STOP: checkpoint missing"

data = torch.load(
    checkpoint, map_location="cpu",
    weights_only=True, mmap=True
)

if isinstance(data, dict) and "state_dict" in data:
    data = data["state_dict"]
elif isinstance(data, dict) and "model_state_dict" in data:
    data = data["model_state_dict"]

assert isinstance(data, dict), "STOP: unexpected checkpoint structure"

targets = {
    "page_embedding.weight": (15, 224),
    "item_embedding.weight": (10727, 112),
    "item_meta_embedding.weight": (523, 32),
    "item_pre_embedding.weight": (10727, 112),
    "page_meta_wide_dense.weight": (32, 1),
    "page_meta_wide_dense.bias": (32,),
}

print("===== SEQUENCE WEIGHT IDENTIFICATION =====")

for suffix, shape in targets.items():
    matches = [
        (k, v) for k, v in data.items()
        if isinstance(v, torch.Tensor)
        and (k == suffix or k.endswith("." + suffix))
        and tuple(v.shape) == shape
    ]

    print(f"\n{suffix} EXPECTED {shape}")
    for key, value in matches:
        print("MATCH:", key, tuple(value.shape))

    if len(matches) != 1:
        print("NEEDS RESOLUTION:", len(matches), "matches")
    else:
        print("UNIQUE MATCH: YES")

print("\nREAD-ONLY CHECK COMPLETE")
print("NO FILES MODIFIED")
PY
