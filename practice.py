podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast, copy, sys
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

source = base / "grecbase_fusion_order_correct_max.py"
target = base / "grecbase_fusion_sibling_fixed_max.py"
assert source.exists()

tree = ast.parse(source.read_text())
fn = next(
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_grecbase_fusion_graph_order_correct"
)

# Find the ACTUAL sibling assignment, without assuming two.
assigns = [
    n for n in ast.walk(fn)
    if isinstance(n, ast.Assign)
    and any(
        isinstance(t, ast.Name) and t.id == "sibling"
        for t in n.targets
    )
]

print("SIBLING ASSIGNMENTS:", len(assigns), flush=True)
assert len(assigns) == 1, "Unexpected source; no patch applied"

assignment = assigns[0]
print("BEFORE:", ast.unparse(assignment)[:350], flush=True)

# Locate the two pooling expressions.
concats = [
    n for n in ast.walk(assignment.value)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Attribute)
    and n.func.attr == "concat"
    and n.args
    and isinstance(n.args[0], ast.List)
    and len(n.args[0].elts) == 2
]
assert len(concats) == 1, "Cannot locate sibling pooling pair"

pair = concats[0].args[0].elts
assert ast.dump(pair[0]) == ast.dump(pair[1]), (
    "Pooling expressions are not duplicates; refusing patch"
)

second = copy.deepcopy(pair[1])
means = [
    n for n in ast.walk(second)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Attribute)
    and n.func.attr == "mean"
    and n.args
    and ast.unparse(n.args[0]) == "sibling_stack"
]
assert len(means) == 1, (
    "Expected exactly one sibling mean operation"
)

means[0].func.attr = "max"
pair[1] = second

print("AFTER:", ast.unparse(assignment)[:350], flush=True)

fn.name = "build_grecbase_fusion_graph_sibling_fixed"

# Save the corrected graph only after real sibling parity passes.
fixed_tree = copy.deepcopy(tree)
fixed_source = ast.unparse(
    ast.fix_missing_locations(fixed_tree)
) + "\n"
compile(fixed_source, str(target), "exec")

# Diagnostic: output eight branches before final attention.
diag = copy.deepcopy(tree)
dfn = next(
    n for n in diag.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_grecbase_fusion_graph_sibling_fixed"
)

found = 0
for block in ast.walk(dfn):
    if not isinstance(block, ast.With):
        continue
    for i, statement in enumerate(block.body):
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == "outs"
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Attribute)
            and statement.value.func.attr == "concat"
        ):
            block.body[i + 1:] = [
                ast.parse("graph.output(outs)").body[0]
            ]
            found += 1
            break

assert found == 1, "Eight-branch fusion not uniquely located"

ns = {
    "__file__": str(target),
    "__name__": "cta_max.sibling_validation",
    "__package__": "cta_max"
}
exec(
    compile(ast.fix_missing_locations(diag),
            str(target), "exec"),
    ns
)

# Existing weights: no re-export or checkpoint conversion.
runner = ast.parse(
    (base / "run_transformer_full_sequence.py").read_text()
)
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
    raise ValueError("Unknown weight expression")

files = None
for n in runner.body:
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

weights = {
    name: WeightData.from_numpy(
        np.load(path).astype(np.float32), name
    )
    for name, path in files.items()
}

for p in sorted(base.rglob("att_pooling.*.npy")):
    weights[p.stem] = WeightData.from_numpy(
        np.load(p).astype(np.float32), p.stem
    )

a = np.load(
    base / "sequence_weights/fn_norm1_g_layer1.npy"
).astype(np.float32)
weights["weight"] = WeightData.from_numpy(a, "weight")
assert len(weights) == 25

# Reuse saved REAL input, not synthetic test inputs.
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
    a = np.asarray(x, dtype=dtype)
    assert a.shape == tuple(shape), (a.shape, shape)
    inputs.append(
        Tensor.from_numpy(
            np.ascontiguousarray(a)
        ).to(device)
    )

for x in data["task_in"]:
    add(x, np.int64, (1,))

for key in ("ihq_in", "jet_name_in", "jet_status_in"):
    add(data[key], np.int64, (1, 50))

for x in data["deep_in"]:
    add(x, np.int64, (1,))

wide = np.stack(
    [x.numpy() for x in data["wide_in"]], axis=1
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
        add(
            data["sibling_deep_in"][:, j, i],
            np.int64, (1,)
        )
    add(
        data["sibling_wide_in"][:, :, i],
        np.float32, (1, 18)
    )

assert len(inputs) == 70

graph = ns[
    "build_grecbase_fusion_graph_sibling_fixed"
](DeviceRef.CPU())
model = InferenceSession(devices=[device]).load(
    graph, weights_registry=weights
)

actual = model.execute(*inputs)[0].to_numpy()
assert actual.shape == (1, 8, 256)
assert np.isfinite(actual).all()

# PyTorch capture was saved with old labels.
# PyTorch's true Sibling occupies position 6,
# previously saved under "ihq".
pt = np.load(base / "real_sanity_pytorch_branches.npz")
expected = pt["ihq"]
sibling = actual[:, 6, :]

diff = np.abs(
    expected.astype(np.float64)
    - sibling.astype(np.float64)
)
match = bool(np.allclose(
    expected, sibling,
    rtol=1e-3, atol=1e-3
))

print("\n=== REAL SIBLING PARITY ===")
print("PYTORCH SHAPE:", expected.shape)
print("MAX SHAPE:", sibling.shape)
print("MEAN DIFF:", float(diff.mean()))
print("MAX DIFF:", float(diff.max()))
print("MATCH:", match)

if match:
    if target.exists():
        assert target.read_text() == fixed_source, (
            "Existing target differs; refusing overwrite"
        )
    else:
        target.write_text(fixed_source)
    print("CORRECTED MAX GRAPH SAVED: PASS")
else:
    print("CORRECTION NOT VERIFIED — NEW GRAPH NOT SAVED")

print("ORIGINAL DS AND WORKING MAX FILES UNCHANGED")
PY
