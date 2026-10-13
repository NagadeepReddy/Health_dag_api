podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast
import sys
import inspect
from pathlib import Path

import numpy as np
from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Shape
from max.graph.weights import WeightData

base = Path("artifacts/v1.168-max/cta_max")
runner = base / "run_transformer_full_sequence.py"
assert runner.is_file(), f"Missing existing runner: {runner}"

WBASE = str(base / "sequence_weights")
assert Path(WBASE).is_dir(), f"Missing weight directory: {WBASE}"

tree = ast.parse(runner.read_text())
weight_files = {}

def evaluate(node):
    return eval(
        compile(ast.Expression(node), str(runner), "eval"),
        {"__builtins__": {}, "WBASE": WBASE},
        {}
    )

for node in tree.body:
    if isinstance(node, ast.Assign):
        if any(isinstance(t, ast.Name) and t.id == "weight_files"
               for t in node.targets):
            weight_files.update(evaluate(node.value))

    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        call = node.value
        if (isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "weight_files"
                and call.func.attr == "update"
                and len(call.args) == 1):
            weight_files.update(evaluate(call.args[0]))

assert weight_files, "Could not extract existing weight mapping"

missing = [(k, p) for k, p in weight_files.items()
           if not Path(p).is_file()]
assert not missing, f"Missing trained weight files: {missing}"

weights = {}
for name, path in weight_files.items():
    arr = np.load(path).astype(np.float32)
    weights[name] = WeightData(
        arr,
        name=name,
        dtype=DType.float32,
        shape=Shape(arr.shape)
    )

# Existing verified RMSNorm compatibility mapping.
norm_path = base / "sequence_weights/fn_norm1_g_layer1.npy"
assert norm_path.is_file()
norm = np.load(norm_path).astype(np.float32)
weights["weight"] = WeightData(
    norm,
    name="weight",
    dtype=DType.float32,
    shape=Shape(norm.shape)
)

print("TRAINED SEQUENCE WEIGHTS REGISTERED:", len(weights), flush=True)
print("PAGE EMBEDDING REGISTERED:",
      "sequence_transformer.page_embedding" in weights, flush=True)

sys.path.insert(0, str(base.parent))

from cta_max.grecbase_fusion_real_shapes_max import (
    build_grecbase_fusion_graph_real_shapes
)

device = CPU()
parameters = inspect.signature(
    build_grecbase_fusion_graph_real_shapes
).parameters

if "device_ref" in parameters:
    graph = build_grecbase_fusion_graph_real_shapes(
        DeviceRef.from_device(device)
    )
else:
    graph = build_grecbase_fusion_graph_real_shapes(device)

print("COMBINED GRAPH CONSTRUCTION: PASS", flush=True)

session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)

print("COMBINED GRAPH WEIGHT LOADING: PASS")
print("COMBINED GRAPH COMPILATION: PASS")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
print("NO FILES MODIFIED")
PY
