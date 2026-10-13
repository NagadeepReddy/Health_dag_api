podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast
import sys
from pathlib import Path

import numpy as np
import torch
from max.driver import CPU, Tensor
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Shape
from max.graph.weights import WeightData

base = Path("artifacts/v1.168-max/cta_max")
checkpoint = Path("artifacts/v1.168/core-artifact/model_0_base.pt")
input_path = base / "real_sanity_model_in.pt"
runner = base / "run_transformer_full_sequence.py"

for p in (checkpoint, input_path, runner):
    assert p.is_file(), f"Missing: {p}"

# Reuse the previously successful trained-weight registration.
loaded = torch.load(checkpoint, map_location="cpu", weights_only=False)
if hasattr(loaded, "state_dict"):
    state = loaded.state_dict()
else:
    state = loaded
    for key in ("state_dict", "model_state_dict", "model"):
        if isinstance(state, dict) and key in state:
            state = state[key]
            if hasattr(state, "state_dict"):
                state = state.state_dict()
            break

assert isinstance(state, dict)

weights = {}

def register(name, value):
    arr = np.ascontiguousarray(value, dtype=np.float32)
    weights[name] = WeightData(
        arr, name=name, dtype=DType.float32,
        shape=Shape(arr.shape)
    )

for name, value in state.items():
    if isinstance(value, torch.Tensor) and value.is_floating_point():
        register(name, value.detach().cpu().numpy())

WBASE = str(base / "sequence_weights")
tree = ast.parse(runner.read_text())
weight_files = {}

def extract(node):
    return eval(
        compile(ast.Expression(node), str(runner), "eval"),
        {"__builtins__": {}, "WBASE": WBASE}, {}
    )

for node in tree.body:
    if isinstance(node, ast.Assign):
        if any(isinstance(t, ast.Name) and t.id == "weight_files"
               for t in node.targets):
            weight_files.update(extract(node.value))
    elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        call = node.value
        if (isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "weight_files"
            and call.func.attr == "update"
            and len(call.args) == 1):
            weight_files.update(extract(call.args[0]))

assert weight_files, "Existing sequence mapping missing"
for name, path in weight_files.items():
    register(name, np.load(path))

register("weight", np.load(
    base / "sequence_weights/fn_norm1_g_layer1.npy"
))

assert "att_pooling.fused_attn_ff_proj.weight" in weights
print("TRAINED WEIGHTS READY:", len(weights), flush=True)

# Existing real CTA input, produced by original DS preprocessing.
data = torch.load(input_path, map_location="cpu", weights_only=False)
assert isinstance(data, dict)

def array(value, dtype, shape, name):
    if isinstance(value, torch.Tensor):
        value = value.detach().cpu().numpy()
    result = np.asarray(value, dtype=dtype)
    assert result.shape == shape, (
        f"{name}: expected {shape}, got {result.shape}"
    )
    return np.ascontiguousarray(result)

inputs = []

def add(value, dtype, shape, name):
    inputs.append(Tensor.from_numpy(array(value, dtype, shape, name)))

# Inputs 0–4: tasks, IHQ and JET.
for i in range(2):
    add(data["task_in"][i], np.int64, (1,), f"task{i}")

for key in ("ihq_in", "jet_name_in", "jet_status_in"):
    add(data[key], np.int64, (1, 50), key)

# Inputs 5–22: main ContextHead (17 deep + 127 wide).
assert len(data["deep_in"]) == 17
for i, value in enumerate(data["deep_in"]):
    add(value, np.int64, (1,), f"deep{i}")

wide = np.stack([
    np.asarray(v).reshape(1) for v in data["wide_in"]
], axis=1)
add(wide, np.float32, (1, 127), "wide")

# Inputs 23–24: NLP.
for key in ("input_ids", "attention_mask"):
    add(data[key], np.int64, (1, 5), key)

# Inputs 25–29: sequence.
for key in ("page_in", "item_in", "item_meta_in"):
    add(data[key], np.int64, (1, 50), key)

page_wide = np.asarray(data["page_meta_wide_in"][0])
page_wide = page_wide.reshape(1, 50, 1)
add(page_wide, np.float32, (1, 50, 1), "page_wide")

# Existing saved CTA rotary frequencies.
inv_path = base / "sequence_weights/fn_rotary_emb_inv_freq.npy"
assert inv_path.is_file(), f"Missing rotary reference: {inv_path}"

inv = np.load(inv_path).astype(np.float32).reshape(-1)
assert inv.shape == (128,), f"Unexpected rotary frequency shape: {inv.shape}"

positions = np.arange(50, dtype=np.float32)
freqs = np.einsum("i,j->ij", positions, inv)
pos = np.concatenate((freqs, freqs), axis=-1)[None, None, :, :]
add(pos, np.float32, (1, 1, 50, 256), "rotary_position")

# Inputs 30–69: ten siblings, four inputs each.
sdeep = np.asarray(data["sibling_deep_in"])
swide = np.asarray(data["sibling_wide_in"])
assert sdeep.shape == (1, 3, 10)
assert swide.shape == (1, 18, 10)

for i in range(10):
    for j in range(3):
        add(
            sdeep[:, j, i], np.int64, (1,),
            f"sibling{i}_deep{j}"
        )
    add(
        swide[:, :, i], np.float32, (1, 18),
        f"sibling{i}_wide"
    )

assert len(inputs) == 70, f"Input count: {len(inputs)}"
print("REAL CTA GRAPH INPUTS: 70", flush=True)

# Reuse the previously compiled graph builder unchanged.
sys.path.insert(0, str(base.parent))

from cta_max.grecbase_fusion_real_shapes_max import (
    build_grecbase_fusion_graph_real_shapes
)

device = CPU()
graph = build_grecbase_fusion_graph_real_shapes(
    DeviceRef.from_device(device)
)

session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)

print("REAL CTA MAX GRAPH COMPILED: PASS", flush=True)

results = model.execute(*inputs)
assert len(results) > 0

for i, result in enumerate(results):
    output = result.to_numpy()
    print("OUTPUT", i, "SHAPE:", output.shape)
    print("OUTPUT", i, "FINITE:", bool(np.isfinite(output).all()))
    assert np.isfinite(output).all()

print("REAL CTA MAX EXECUTION: PASS")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
print("NO FILES MODIFIED")
PY
