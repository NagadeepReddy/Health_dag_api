REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import torch
from pathlib import Path

root = Path("artifacts/v1.113-max/maxserve_bplan_extension")
data = torch.load(root / "bplan_neural_inputs.pt",
                  map_location="cpu", weights_only=True)

print("=== REAL BPLAN INPUT SHAPES ===")
for name, value in data.items():
    if isinstance(value, (list, tuple)):
        print(name, [tuple(x.shape) for x in value])
    elif isinstance(value, torch.Tensor):
        print(name, tuple(value.shape))

print("\n=== MAX GRAPH SEQUENCE DIMENSIONS ===")
dev = root / "bplan_max_dev"
for filename in ("grecbase_fusion_full_head_72_max.py",
                 "run_real_sanity_input_adapter.py"):
    for i, line in enumerate((dev / filename).read_text().splitlines(), 1):
        if any(term in line for term in (
            "page_wide", "page_meta_wide", "50", "20", "valid_length"
        )):
            print(f"{filename}:{i}: {line.strip()[:150]}")
PY
