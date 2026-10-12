podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, ast
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

# 1. Preserve original files and correct only the MAX output boundary.
old_helper = base / "grecbase_get_path_max.py"
new_helper = base / "grecbase_get_path_reference_max.py"
old_graph = base / "grecbase_fusion_real_shapes_max.py"
new_graph = base / "grecbase_fusion_parity_max.py"

ht = ast.parse(old_helper.read_text())
functions = [
    n for n in ht.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "grecbase_get_path_max"
]
assert len(functions) == 1
fn = functions[0]

last = fn.body[-1]
assert isinstance(last, ast.Return)
assert isinstance(last.value, ast.Call)
assert isinstance(last.value.func, ast.Name)
assert last.value.func.id == "linear"
assert isinstance(last.value.args[0], ast.Name)
assert last.value.args[0].id == "hidden"
assert ast.literal_eval(last.value.args[1]) == "remove_tasks_dense2"

fn.name = "grecbase_get_path_reference_max"
last.value = ast.Name(id="hidden", ctx=ast.Load())

helper_src = ast.unparse(ast.fix_missing_locations(ht)) + "\n"

gt = ast.parse(old_graph.read_text())
builders = [
    n for n in gt.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_grecbase_fusion_graph_real_shapes"
]
assert len(builders) == 1
builders[0].name = "build_grecbase_fusion_graph_parity"

imports = [
    n for n in gt.body
    if isinstance(n, ast.ImportFrom)
    and n.module == "cta_max.grecbase_get_path_max"
]
assert len(imports) == 1
assert len(imports[0].names) == 1
assert imports[0].names[0].name == "grecbase_get_path_max"

imports[0].module = "cta_max.grecbase_get_path_reference_max"
imports[0].names[0].name = "grecbase_get_path_reference_max"

calls = [
    n for n in ast.walk(builders[0])
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id == "grecbase_get_path_max"
]
assert len(calls) == 1
calls[0].func.id = "grecbase_get_path_reference_max"

graph_src = ast.unparse(ast.fix_missing_locations(gt)) + "\n"

compile(helper_src, str(new_helper), "exec")
compile(graph_src, str(new_graph), "exec")

for p, content in (
    (new_helper, helper_src),
    (new_graph, graph_src)
):
    if p.exists():
        assert p.read_text() == content, (
            f"Existing file differs; refusing overwrite: {p}"
        )
    else:
        p.write_text(content)

print("ORIGINAL GET_PATH AND GRAPH PRESERVED")
print("CORRECTED OUTPUT BOUNDARY: READY", flush=True)

from cta_max.grecbase_fusion_parity_max import (
    build_grecbase_fusion_graph_parity
)

# 2. Reuse the successful 25-weight MAX registry.
runner = base / "run_transformer_full_sequence.py"
rt = ast.parse(runner.read_text())
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

files = None
for n in rt.body:
    if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "weight_files"
        for t in n.targets
    ):
        files = resolve(n.value)
    elif (
        isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Attribute)
        and isinstance(n.value.func.value, ast.Name)
        and n.value.func.value.id == "weight_files"
        and n.value.func.attr == "update"
    ):
        assert files is not None
        files.update(resolve(n.value.args[0]))

assert len(files) == 18

weights = {}
for name, path in files.items():
    weights[name] = WeightData.from_numpy(
        np.load(path).astype(np.float32), name
    )

for p in sorted(base.rglob("att_pooling.*.npy")):
    assert p.stem not in weights
    weights[p.stem] = WeightData.from_numpy(
        np.load(p).astype(np.float32), p.stem
    )

a = np.load(
    base / "sequence_weights/fn_norm1_g_layer1.npy"
).astype(np.float32)
weights["weight"] = WeightData.from_numpy(a, "weight")
assert len(weights) == 25

# 3. Load the actual preprocessed request.
data = torch.load(
    base / "real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=True
)
assert len(data) == 17

device = CPU()
inputs = []

def add(value, dtype, shape, name):
    if isinstance(value, torch.Tensor):
        value = value.detach().cpu().numpy()
    arr = np.asarray(value, dtype=dtype)
    assert arr.shape == tuple(shape), (name, arr.shape, shape)
    inputs.append(
        Tensor.from_numpy(np.ascontiguousarray(arr)).to(device)
    )

for i in range(2):
    add(data["task_in"][i], np.int64, (1,), f"task{i}")

for key in ("ihq_in", "jet_name_in", "jet_status_in"):
    add(data[key], np.int64, (1, 50), key)

for i, x in enumerate(data["deep_in"]):
    add(x, np.int64, (1,), f"deep{i}")

wide = np.stack(
    [x.detach().cpu().numpy() for x in data["wide_in"]],
    axis=1
)
add(wide, np.float32, (1, 127), "wide")

add(data["input_ids"], np.int64, (1, 5), "input_ids")
add(data["attention_mask"], np.int64, (1, 5), "mask")

for key in ("page_in", "item_in", "item_meta_in"):
    add(data[key], np.int64, (1, 50), key)

page_wide = data["page_meta_wide_in"][0].numpy()
add(page_wide[:, :, None], np.float32, (1, 50, 1), "page_wide")

# Reuse previously successful MAX rotary-position generation.
inv = np.load(
    base / "sequence_weights/fn_rotary_emb_inv_freq.npy"
).astype(np.float32)
assert inv.shape == (128,)
freq = np.arange(50, dtype=np.float32)[:, None] * inv[None, :]
pos = np.concatenate([freq, freq], axis=-1)[None, None, :, :]
add(pos, np.float32, (1, 1, 50, 256), "position")

sdeep = data["sibling_deep_in"]
swide = data["sibling_wide_in"]
assert tuple(sdeep.shape) == (1, 3, 10)
assert tuple(swide.shape) == (1, 18, 10)

for i in range(10):
    for j in range(3):
        add(sdeep[:, j, i], np.int64, (1,), f"sibling{i}_{j}")
    add(swide[:, :, i], np.float32, (1, 18), f"sibling{i}_wide")

assert len(inputs) == 70

# 4. Execute and compare against the saved original PyTorch output.
graph = build_grecbase_fusion_graph_parity(DeviceRef.CPU())
session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)
print("CORRECTED MAX GRAPH COMPILATION: PASS", flush=True)

actual = model.execute(*inputs)[0].to_numpy()
expected = np.load(base / "real_sanity_pytorch_output.npy")

print("PYTORCH SHAPE:", expected.shape)
print("MAX SHAPE:", actual.shape)
print("PYTORCH FINITE:", bool(np.isfinite(expected).all()))
print("MAX FINITE:", bool(np.isfinite(actual).all()))

assert expected.shape == actual.shape == (1, 2048)
assert np.isfinite(expected).all()
assert np.isfinite(actual).all()

delta = np.abs(
    expected.astype(np.float64) - actual.astype(np.float64)
)

print("MEAN ABS DIFFERENCE:", float(delta.mean()))
print("MAX ABS DIFFERENCE:", float(delta.max()))
print(
    "NUMERICAL MATCH (rtol=1e-3, atol=1e-3):",
    bool(np.allclose(expected, actual, rtol=1e-3, atol=1e-3))
)

np.save(base / "real_sanity_max_2048.npy", actual)
print("CORRECTED REAL MAX OUTPUT SAVED")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
