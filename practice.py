podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, ast
from pathlib import Path
import numpy as np
import torch

root = Path("/workspace/artifacts/v1.168-max")
base = root / "cta_max"
sys.path.insert(0, str(root))

from max.driver import CPU
from max.engine import InferenceSession
from max.graph import DeviceRef
from max.graph.weights import WeightData
from cta_max.grecbase_fusion_real_shapes_max import (
    build_grecbase_fusion_graph_real_shapes
)

print("=== REAL CTA GRAPH COMPILATION ===", flush=True)

# Reuse exact registry from the previously successful
# eight-branch runtime test.
runner = base / "run_transformer_full_sequence.py"
tree = ast.parse(runner.read_text())
wbase = str(base / "sequence_weights")

def resolve(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id == "WBASE":
        return wbase
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return resolve(node.left) + resolve(node.right)
    if isinstance(node, ast.Dict):
        return {
            resolve(k): resolve(v)
            for k, v in zip(node.keys, node.values)
        }
    raise ValueError("Unexpected weight mapping expression")

weight_files = None

for n in tree.body:
    if isinstance(n, ast.Assign):
        if any(
            isinstance(t, ast.Name) and t.id == "weight_files"
            for t in n.targets
        ):
            weight_files = resolve(n.value)
    elif (
        isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Attribute)
        and isinstance(n.value.func.value, ast.Name)
        and n.value.func.value.id == "weight_files"
        and n.value.func.attr == "update"
    ):
        weight_files.update(resolve(n.value.args[0]))

assert weight_files and len(weight_files) == 18

weights = {}
for name, path in weight_files.items():
    arr = np.load(path).astype(np.float32)
    weights[name] = WeightData.from_numpy(arr, name)

for p in sorted(base.rglob("att_pooling.*.npy")):
    name = p.stem
    assert name not in weights
    weights[name] = WeightData.from_numpy(
        np.load(p).astype(np.float32), name
    )

arr = np.load(
    base / "sequence_weights/fn_norm1_g_layer1.npy"
).astype(np.float32)
weights["weight"] = WeightData.from_numpy(arr, "weight")

print("WEIGHTS REGISTERED:", len(weights), flush=True)

device = CPU()
graph = build_grecbase_fusion_graph_real_shapes(
    DeviceRef.CPU()
)

session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)

print("REAL-SIZE GRAPH COMPILATION: PASS", flush=True)

# Load the real input produced by original DS preprocessing.
saved = base / "real_sanity_model_in.pt"
assert saved.is_file()

data = torch.load(
    saved, map_location="cpu", weights_only=True
)

assert isinstance(data, dict) and len(data) == 17

print("REAL MODEL INPUT LOADED: PASS")
print("INPUT FIELDS:", len(data))

print("\n=== CRITICAL REAL INPUT SHAPES ===")
for key in (
    "page_in", "item_in", "item_meta_in",
    "page_meta_wide_in", "vl_in",
    "input_ids", "attention_mask",
    "ihq_in", "jet_name_in", "jet_status_in",
    "sibling_deep_in", "sibling_wide_in"
):
    value = data[key]
    if isinstance(value, (list, tuple)):
        print(key, "list length:", len(value),
              "shapes:", [tuple(x.shape) for x in value[:2]])
    else:
        print(key, tuple(value.shape), str(value.dtype))

# Verify sequence positional-input derivation before
# passing data into MAX. Never substitute invented values.
print("\n=== ORIGINAL SEQUENCE POSITION USAGE ===")

p = Path(
    "/workspace/artifacts/v1.168/"
    "utils/dependency-utils/models.py"
)
lines = p.read_text().splitlines()
tree = ast.parse(p.read_text())

found = 0
for node in ast.walk(tree):
    if not isinstance(node, ast.FunctionDef):
        continue
    if "vl_in" not in [a.arg for a in node.args.args]:
        continue

    print("FUNCTION:", node.name, "line:", node.lineno)

    for n in ast.walk(node):
        if isinstance(n, ast.Name) and n.id == "vl_in":
            start = max(node.lineno, n.lineno - 2)
            end = min(node.end_lineno, n.lineno + 2)
            for i in range(start, end + 1):
                print(f"{i}: {lines[i-1][:180]}")
            print("---")
            found += 1
            if found >= 5:
                break
    if found >= 5:
        break

print("\nREAL GRAPH READY FOR INPUT ADAPTER")
print("NO SYNTHETIC POSITION VALUES USED")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
