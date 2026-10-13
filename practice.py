podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast
import sys
from pathlib import Path

import numpy as np
import torch
from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Shape
from max.graph.weights import WeightData

base = Path("artifacts/v1.168-max/cta_max")
checkpoint = Path("artifacts/v1.168/core-artifact/model_0_base.pt")
runner = base / "run_transformer_full_sequence.py"

assert checkpoint.is_file(), f"Missing checkpoint: {checkpoint}"
assert runner.is_file(), f"Missing existing runner: {runner}"

def register(name, value):
    arr = np.asarray(value, dtype=np.float32)
    weights[name] = WeightData(
        arr,
        name=name,
        dtype=DType.float32,
        shape=Shape(arr.shape)
    )

# 1. Load actual trained model weights.
loaded = torch.load(checkpoint, map_location="cpu", weights_only=False)

if hasattr(loaded, "state_dict"):
    state = loaded.state_dict()
elif isinstance(loaded, dict):
    state = loaded
    for key in ("state_dict", "model_state_dict", "model"):
        if key in state:
            state = state[key]
            if hasattr(state, "state_dict"):
                state = state.state_dict()
            break
else:
    raise TypeError(f"Unexpected checkpoint type: {type(loaded)}")

assert isinstance(state, dict)

weights = {}
for name, value in state.items():
    if isinstance(value, torch.Tensor) and value.is_floating_point():
        register(name, value.detach().cpu().float().numpy())

print("CHECKPOINT WEIGHTS REGISTERED:", len(weights), flush=True)

required = "att_pooling.fused_attn_ff_proj.weight"

if required not in weights:
    print("EXACT KEY NOT IN CHECKPOINT")
    print("RELATED CHECKPOINT KEYS:")
    for name in weights:
        if "att_pooling" in name or "fused_attn_ff_proj" in name:
            print(name)
    raise SystemExit("STOP: Need exact checkpoint mapping; no guessed weights used")

print("ATTENTION POOLING WEIGHT: FOUND", flush=True)

# 2. Preserve previously successful sequence-weight registration.
WBASE = str(base / "sequence_weights")
tree = ast.parse(runner.read_text())
weight_files = {}

def extract(node):
    return eval(
        compile(ast.Expression(node), str(runner), "eval"),
        {"__builtins__": {}, "WBASE": WBASE},
        {}
    )

for node in tree.body:
    if isinstance(node, ast.Assign):
        if any(isinstance(t, ast.Name) and t.id == "weight_files"
               for t in node.targets):
            weight_files.update(extract(node.value))
    elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        call = node.value
        if (
            isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "weight_files"
            and call.func.attr == "update"
            and len(call.args) == 1
        ):
            weight_files.update(extract(call.args[0]))

assert weight_files, "Existing sequence mappings not found"

for name, path in weight_files.items():
    assert Path(path).is_file(), f"Missing: {path}"
    register(name, np.load(path))

print("SEQUENCE MAPPINGS PRESERVED:", len(weight_files), flush=True)

# Preserve previously proven RMSNorm registry alias.
norm_path = base / "sequence_weights/fn_norm1_g_layer1.npy"
assert norm_path.is_file()
register("weight", np.load(norm_path))

print("TOTAL WEIGHT REGISTRY:", len(weights), flush=True)
print("PAGE EMBEDDING:",
      "sequence_transformer.page_embedding" in weights, flush=True)

# 3. Compile the existing combined graph without editing source.
sys.path.insert(0, str(base.parent))

from cta_max.grecbase_fusion_real_shapes_max import (
    build_grecbase_fusion_graph_real_shapes
)

device = CPU()
graph = build_grecbase_fusion_graph_real_shapes(
    DeviceRef.from_device(device)
)

print("COMBINED GRAPH CONSTRUCTION: PASS", flush=True)

session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)

print("COMBINED GRAPH COMPILATION: PASS")
print("TRAINED ATTENTION WEIGHT: REGISTERED")
print("ORIGINAL PYTORCH AND DS CODE: UNCHANGED")
print("NO FILES MODIFIED")
PY
