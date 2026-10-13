podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import torch

base = Path("artifacts/v1.168-max/cta_max")
data = torch.load(base / "real_sanity_model_in.pt",
                  map_location="cpu", weights_only=True)

print("=== REAL VALID SEQUENCE LENGTH ===")
v = data.get("vl_in", data.get("v1_in"))
print("valid_length:", v)
print("sequence capacity: 50")

files = [
    Path("artifacts/v1.168/utils/dependency-utils/models.py"),
    base / "parallel_transformer_block_2layers.py",
    base / "grecbase_fusion_order_correct_max.py",
]
terms = ("valid_length", "vl_in", "padding_mask",
         "masked_fill", "softmax", "causal_mask")

for p in files:
    print("\n===", p.name, "===")
    if not p.exists():
        print("FILE NOT FOUND")
        continue

    lines = p.read_text().splitlines()
    hits = [i for i, s in enumerate(lines)
            if any(t in s.lower() for t in terms)]
    shown = set()

    for i in hits[:18]:
        for j in range(max(0, i-4), min(len(lines), i+6)):
            if j not in shown:
                print(f"{j+1}: {lines[j]}")
                shown.add(j)

print("\nREAD ONLY — NOTHING MODIFIED")
PY
