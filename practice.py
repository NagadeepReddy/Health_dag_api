podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import ast
import torch

model = Path("artifacts/v1.168/utils/dependency-utils/models.py")
source = model.read_text()
tree = ast.parse(source)

for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "GRecBase":
        print("=== ORIGINAL GRecBase SIGNATURES ===")
        for fn in node.body:
            if isinstance(fn, ast.FunctionDef) and fn.name in ("__init__", "forward"):
                print(fn.name, ast.unparse(fn.args))
        break
else:
    raise SystemExit("STOP: Original GRecBase not found")

pipeline = Path("artifacts/v1.168/core-artifact/pipeline.py")
lines = pipeline.read_text().splitlines()
matches = [
    i for i, line in enumerate(lines)
    if "self.model_base(" in line
]
print("\n=== ORIGINAL MODEL CALL ===")
for i in matches:
    for j in range(max(0, i-2), min(len(lines), i+24)):
        print(f"{j+1}: {lines[j]}")

data = torch.load(
    "artifacts/v1.168-max/cta_max/real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=True
)

print("\n=== SAVED REAL MODEL INPUTS ===")
for key, value in data.items():
    if isinstance(value, torch.Tensor):
        description = tuple(value.shape)
    elif isinstance(value, (list, tuple)):
        description = [
            tuple(v.shape) if isinstance(v, torch.Tensor) else type(v).__name__
            for v in value
        ]
    else:
        description = type(value).__name__
    print(key, description)

print("\nREAD ONLY — NO FILES MODIFIED")
PY
