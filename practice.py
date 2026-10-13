podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast
from pathlib import Path
import numpy as np
import torch

root = Path("artifacts/v1.168")
base = Path("artifacts/v1.168-max/cta_max")
source = root / "utils/dependency-utils/models.py"

data = torch.load(
    base / "real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=True
)

vl = data["vl_in"].detach().cpu().numpy()
print("=== REAL CTA VL INPUT ===")
print("SHAPE:", vl.shape)
print("VALUES:", vl[0].tolist())
print("EQUAL TO 0..49:", bool(
    np.array_equal(vl[0], np.arange(50))
))
print("UNIQUE:", np.unique(vl).tolist())

tree = ast.parse(source.read_text())

print("\n=== ORIGINAL TRANSFORMER BLOCK ===")
for cls in ast.walk(tree):
    if not isinstance(cls, ast.ClassDef):
        continue

    if "TransformerBlock" not in cls.name:
        continue

    print("\nCLASS:", cls.name)

    for fn in cls.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        if fn.name != "forward":
            continue

        print("ARGS:", ast.unparse(fn.args))
        for stmt in fn.body:
            print(ast.unparse(stmt).replace("\n", " ")[:600])

print("\n=== ORIGINAL POSITION / ROTARY REFERENCES ===")
lines = source.read_text().splitlines()

for i, line in enumerate(lines):
    if any(term in line for term in (
        "apply_rotary_pos_emb(",
        "rotary_emb(",
        "position_ids",
        "self.ptransformer ="
    )):
        print(f"{i+1}: {line.strip()[:180]}")
        if "self.ptransformer =" in line:
            for extra in lines[i+1:i+5]:
                print("  ", extra.strip()[:180])

print("\n=== MAX POSITION GENERATION ===")
p = base / "grecbase_fusion_real_shapes_max.py"
for i, line in enumerate(p.read_text().splitlines(), 1):
    if any(term in line for term in (
        "pos =", "inv_freq", "arange",
        "block0(", "block1("
    )):
        print(f"{i}: {line.strip()[:180]}")

print("\nREAD ONLY — NOTHING MODIFIED")
PY
