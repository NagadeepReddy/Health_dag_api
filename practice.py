podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import ast
import torch
from pathlib import Path

root = Path("artifacts/v1.168/utils/dependency-utils")
found = []

for p in root.rglob("*.py"):
    try:
        source = p.read_text()
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "FFSwiGLU":
            found.append((p, ast.get_source_segment(source, node)))

print("===== FFSwiGLU IMPLEMENTATION =====")
for p, code in found:
    print("FILE:", p)
    print(code)
if not found:
    print("NOT FOUND IN dependency-utils")

p = Path("artifacts/v1.168/core-artifact/model_0_base.pt")
data = torch.load(p, map_location="cpu", weights_only=True, mmap=True)
if "state_dict" in data:
    data = data["state_dict"]
elif "model_state_dict" in data:
    data = data["model_state_dict"]

print("\n===== FINAL OUTPUT WEIGHTS =====")
for key, value in data.items():
    if "remove_tasks_dense1" in key or "remove_tasks_act1" in key:
        print(key, tuple(value.shape))

print("\nREAD-ONLY — NO FILES MODIFIED")
PY
