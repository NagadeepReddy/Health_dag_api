podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import ast
from pathlib import Path
import numpy as np
import torch

root = Path("/workspace/artifacts/v1.168-max")
base = root / "cta_max"
sys.path.insert(0, str(root))

from max.driver import CPU, Tensor
from max.engine import InferenceSession
from max.graph import DeviceRef
from max.graph.weights import WeightData
from cta_max.grecbase_fusion_real_shapes_max import (
    build_grecbase_fusion_graph_real_shapes
)

# Load real inputs from the successful DS preprocessing.
saved = base / "real_sanity_model_in.pt"
assert saved.is_file()

data = torch.load(
    saved, map_location="cpu", weights_only=True
)
assert isinstance(data, dict) and len(data) == 17

print("REAL DS INPUT LOADED: PASS", flush=True)

# Reuse the exact successful sequence weight registry.
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
    raise ValueError("Unexpected registry expression")

weight_files = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        if any(
            isinstance(t, ast.Name) and t.id == "weight_files"
            for t in node.targets
        ):
            weight_files = resolve(node.value)
    elif (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and isinstance(node.value.func.value, ast.Name)
        and node.value.func.value.id == "weight_files"
        and node.value.func.attr == "update"
    ):
        assert weight_files is not None
        weight_files.update(resolve(node.value.args[0]))

assert weight_files and len(weight_files) == 18

weights = {}
for name, path in weight_files.items():
    arr = np.load(path).astype(np.float32)
    weights[name] = WeightData.from_numpy(arr, name)

for p in sorted(base.rglob("att_pooling.*.npy")):
    assert p.stem not in weights
    arr = np.load(p).astype(np.float32)
    weights[p.stem] = WeightData.from_numpy(arr, p.stem)

arr = np.load(
    base / "sequence_weights/fn_norm1_g_layer1.npy"
).astype(np.float32)
weights["weight"] = WeightData.from_numpy(arr, "weight")

assert len(weights) == 25
print("EXISTING WEIGHT REGISTRY: PASS", flush=True)

# Generate rotary positions with the existing MAX runner's
# already-validated formula. PyTorch vl_in equivalence
# remains a separate parity requirement.
page = data["page_in"]
seq_len = int(page.shape[1])
assert seq_len == 50

inv = np.load(
    base / "sequence_weights/fn_rotary_emb_inv_freq.npy"
).astype(np.float32)
assert inv.shape == (128,), inv.shape

seq = np.arange(seq_len, dtype=np.float32)
freqs = np.einsum("i,j->ij", seq, inv)
pos = np.concatenate([freqs, freqs], axis=-1)
pos = pos[None, None, :, :].astype(np.float32)

assert pos.shape == (1, 1, 50, 256)

device = CPU()
inputs = []

def add(value, dtype, shape, label):
    if isinstance(value, torch.Tensor):
        arr = value.detach().cpu().numpy()
    else:
        arr = np.asarray(value)

    arr = np.asarray(arr, dtype=dtype)
    assert tuple(arr.shape) == tuple(shape), (
        label, arr.shape, shape
    )

    inputs.append(
        Tensor.from_numpy(
            np.ascontiguousarray(arr)
        ).to(device)
    )

# Original model's task, IHQ and JET inputs.
for i in range(2):
    add(data["task_in"][i], np.int64, (1,),
        f"task{i}")

for key in ("ihq_in", "jet_name_in", "jet_status_in"):
    add(data[key], np.int64, (1, 50), key)

# Main context: 17 deep features and 127 wide features.
assert len(data["deep_in"]) == 17
for i, value in enumerate(data["deep_in"]):
    add(value, np.int64, (1,), f"deep{i}")

assert len(data["wide_in"]) == 127
wide = np.stack(
    [
        v.detach().cpu().numpy()
        for v in data["wide_in"]
    ],
    axis=1
)
add(wide, np.float32, (1, 127), "wide")

# NLP/BERT.
add(data["input_ids"], np.int64, (1, 5), "input_ids")
add(
    data["attention_mask"], np.int64,
    (1, 5), "attention_mask"
)

# Sequence branch.
for key in ("page_in", "item_in", "item_meta_in"):
    add(data[key], np.int64, (1, 50), key)

assert len(data["page_meta_wide_in"]) == 1
page_wide = (
    data["page_meta_wide_in"][0]
    .detach().cpu().numpy()
)
add(
    page_wide[:, :, None],
    np.float32, (1, 50, 1), "page_meta_wide"
)
add(pos, np.float32, (1, 1, 50, 256), "rotary_pos")

# Ten actual sibling entries, without truncation.
sdeep = data["sibling_deep_in"]
swide = data["sibling_wide_in"]

assert tuple(sdeep.shape) == (1, 3, 10)
assert tuple(swide.shape) == (1, 18, 10)

for i in range(10):
    for j in range(3):
        add(
            sdeep[:, j, i],
            np.int64, (1,), f"sibling{i}_deep{j}"
        )
    add(
        swide[:, :, i],
        np.float32, (1, 18), f"sibling{i}_wide"
    )

assert len(inputs) == 70, len(inputs)
print("REAL FEATURE MAPPING: PASS — 70 GRAPH INPUTS",
      flush=True)

# Execute the previously compiled real-size graph.
graph = build_grecbase_fusion_graph_real_shapes(
    DeviceRef.CPU()
)
session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)

print("REAL-SIZE MAX COMPILATION: PASS", flush=True)

result = model.execute(*inputs)[0].to_numpy()

print("REAL INPUT OUTPUT SHAPE:", result.shape)
print("FINITE:", bool(np.isfinite(result).all()))

assert result.shape == (1, 10819), result.shape
assert np.isfinite(result).all()

output = base / "real_sanity_max_output.npy"
np.save(output, result)

print("REAL-INPUT MAX RUNTIME: PASS")
print("OUTPUT SAVED:", output)
print("ORIGINAL PYTORCH AND DS SOURCE UNCHANGED")
print("NUMERICAL PARITY: NOT YET ESTABLISHED")
PY
