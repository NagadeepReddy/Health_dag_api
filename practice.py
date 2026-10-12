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

source = base / "grecbase_fusion_parity_max.py"
reference = base / "real_sanity_pytorch_branches.npz"

assert source.is_file()
assert reference.is_file()

# Capture the MAX branches immediately BEFORE moe_norm1.
# Construct this diagnostic graph in memory only.
tree = ast.parse(source.read_text())

builders = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_grecbase_fusion_graph_parity"
]
assert len(builders) == 1
fn = builders[0]

found = 0

for node in ast.walk(fn):
    if not isinstance(node, ast.With):
        continue

    for i, stmt in enumerate(node.body):
        if not isinstance(stmt, ast.Assign):
            continue

        if (
            len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and stmt.targets[0].id == "outs"
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Name)
            and stmt.value.func.id == "norm"
            and len(stmt.value.args) == 2
            and isinstance(stmt.value.args[1], ast.Constant)
            and stmt.value.args[1].value == "moe_norm1"
        ):
            node.body.insert(
                i,
                ast.parse("pre_norm_branches = outs").body[0]
            )
            found += 1
            break

assert found == 1, (
    "Cannot uniquely locate original branch fusion; "
    "no files modified"
)

outputs = [
    n for n in ast.walk(fn)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Attribute)
    and isinstance(n.func.value, ast.Name)
    and n.func.value.id == "graph"
    and n.func.attr == "output"
]
assert len(outputs) == 1

outputs[0].args = [
    ast.Name(id="pre_norm_branches", ctx=ast.Load())
]

code = compile(
    ast.fix_missing_locations(tree),
    str(source), "exec"
)
ns = {
    "__file__": str(source),
    "__name__": "cta_max.branch_diagnostic",
    "__package__": "cta_max"
}
exec(code, ns)

# Reuse the existing sequence weight registry.
runner = base / "run_transformer_full_sequence.py"
rt = ast.parse(runner.read_text())
wbase = str(base / "sequence_weights")

def resolve(n):
    if isinstance(n, ast.Constant):
        return n.value
    if isinstance(n, ast.Name) and n.id == "WBASE":
        return wbase
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
        return resolve(n.left) + resolve(n.right)
    if isinstance(n, ast.Dict):
        return {
            resolve(k): resolve(v)
            for k, v in zip(n.keys, n.values)
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
        files.update(resolve(n.value.args[0]))

assert files and len(files) == 18

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

# Reuse saved real DS model inputs.
data = torch.load(
    base / "real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=True
)

device = CPU()
inputs = []

def add(x, dtype, shape):
    if isinstance(x, torch.Tensor):
        x = x.detach().cpu().numpy()
    arr = np.asarray(x, dtype=dtype)
    assert arr.shape == tuple(shape), (arr.shape, shape)
    inputs.append(
        Tensor.from_numpy(np.ascontiguousarray(arr)).to(device)
    )

for i in range(2):
    add(data["task_in"][i], np.int64, (1,))

for key in ("ihq_in", "jet_name_in", "jet_status_in"):
    add(data[key], np.int64, (1, 50))

for x in data["deep_in"]:
    add(x, np.int64, (1,))

wide = np.stack(
    [x.detach().cpu().numpy() for x in data["wide_in"]],
    axis=1
)
add(wide, np.float32, (1, 127))

add(data["input_ids"], np.int64, (1, 5))
add(data["attention_mask"], np.int64, (1, 5))

for key in ("page_in", "item_in", "item_meta_in"):
    add(data[key], np.int64, (1, 50))

page_wide = data["page_meta_wide_in"][0].numpy()
add(page_wide[:, :, None], np.float32, (1, 50, 1))

inv = np.load(
    base / "sequence_weights/fn_rotary_emb_inv_freq.npy"
).astype(np.float32)
freq = np.arange(50, dtype=np.float32)[:, None] * inv[None, :]
pos = np.concatenate([freq, freq], axis=-1)[None, None, :, :]
add(pos, np.float32, (1, 1, 50, 256))

for i in range(10):
    for j in range(3):
        add(data["sibling_deep_in"][:, j, i], np.int64, (1,))
    add(data["sibling_wide_in"][:, :, i], np.float32, (1, 18))

assert len(inputs) == 70

graph = ns["build_grecbase_fusion_graph_parity"](DeviceRef.CPU())
model = InferenceSession(devices=[device]).load(
    graph, weights_registry=weights
)

actual = model.execute(*inputs)[0].to_numpy()
assert actual.shape == (1, 8, 256), actual.shape

names = [
    "sequence", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
]

print("\n=== REAL PYTORCH VS MAX BRANCH COMPARISON ===")
print(f"{'BRANCH':<12} {'MEAN DIFF':>14} {'MAX DIFF':>14} {'MATCH':>8}")

ref = np.load(reference)
results = []

for i, name in enumerate(names):
    expected = ref[name]
    value = actual[:, i, :]

    assert expected.shape == value.shape == (1, 256)
    assert np.isfinite(value).all()

    diff = np.abs(
        expected.astype(np.float64)
        - value.astype(np.float64)
    )

    mean = float(diff.mean())
    maximum = float(diff.max())
    match = bool(np.allclose(
        expected, value, rtol=1e-3, atol=1e-3
    ))

    results.append((name, mean, maximum, match))
    print(
        f"{name:<12} {mean:>14.8f} "
        f"{maximum:>14.8f} {str(match):>8}"
    )

out = base / "real_sanity_max_branches.npz"
np.savez(
    out,
    **{name: actual[:, i, :] for i, name in enumerate(names)}
)

print("\nLARGEST DIFFERENCE:",
      max(results, key=lambda x: x[2])[0])
print("MAX BRANCH OUTPUTS SAVED:", out)
print("ORIGINAL DS AND WORKING MAX FILES UNCHANGED")
PY
