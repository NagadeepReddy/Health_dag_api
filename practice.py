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
assert source.is_file()

tree = ast.parse(source.read_text())
fns = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_grecbase_fusion_graph_order_correct"
]
assert len(fns) == 1
fn = fns[0]

assigns = [
    n for n in ast.walk(fn)
    if isinstance(n, ast.Assign)
    and len(n.targets) == 1
    and isinstance(n.targets[0], ast.Name)
    and n.targets[0].id == "sibling"
]
assert len(assigns) == 2, len(assigns)

# Existing: concatenate the mean with itself.
old = assigns[-1].value
assert ast.unparse(old) == (
    "ops.concat([sibling, sibling], axis=-1)"
), ast.unparse(old)

# Original PyTorch uses mean + max pooling.
assigns[-1].value = ast.parse(
    "ops.concat([sibling, "
    "ops.reshape(ops.max(sibling_stack, axis=1), "
    "[1, 1, 128])], axis=-1)",
    mode="eval"
).body

fn.name = "build_grecbase_fusion_graph_sibling_fixed"
fixed = ast.unparse(ast.fix_missing_locations(tree)) + "\n"
compile(fixed, str(target), "exec")

if target.exists():
    assert target.read_text() == fixed, "Target differs; no overwrite"
else:
    target.write_text(fixed)

print("SIBLING MEAN + MAX FIX SAVED")

# Create an eight-branch diagnostic graph in memory.
diag = copy.deepcopy(tree)
dfn = next(
    n for n in diag.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_grecbase_fusion_graph_sibling_fixed"
)

located = 0
for block in ast.walk(dfn):
    if not isinstance(block, ast.With):
        continue
    for i, stmt in enumerate(block.body):
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and stmt.targets[0].id == "outs"
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Attribute)
            and stmt.value.func.attr == "concat"
        ):
            block.body[i+1:] = [
                ast.parse("graph.output(outs)").body[0]
            ]
            located += 1
            break
assert located == 1, located

ns = {
    "__file__": str(target),
    "__name__": "cta_max.sibling_check",
    "__package__": "cta_max"
}
exec(compile(ast.fix_missing_locations(diag),
             str(target), "exec"), ns)

# Reuse the existing validated weight registry.
runner = ast.parse(
    (base / "run_transformer_full_sequence.py").read_text()
)
wbase = str(base / "sequence_weights")

def resolve(n):
    if isinstance(n, ast.Constant): return n.value
    if isinstance(n, ast.Name) and n.id == "WBASE": return wbase
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
        return resolve(n.left) + resolve(n.right)
    if isinstance(n, ast.Dict):
        return {resolve(k): resolve(v)
                for k, v in zip(n.keys, n.values)}
    raise ValueError("Unexpected weight expression")

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

assert len(files) == 18
weights = {
    k: WeightData.from_numpy(np.load(v).astype(np.float32), k)
    for k, v in files.items()
}

for p in sorted(base.rglob("att_pooling.*.npy")):
    weights[p.stem] = WeightData.from_numpy(
        np.load(p).astype(np.float32), p.stem
    )

a = np.load(base/"sequence_weights/fn_norm1_g_layer1.npy")
weights["weight"] = WeightData.from_numpy(
    a.astype(np.float32), "weight"
)
assert len(weights) == 25

data = torch.load(
    base/"real_sanity_model_in.pt",
    map_location="cpu", weights_only=True
)

device = CPU()
inputs = []

def add(x, dtype, shape):
    if isinstance(x, torch.Tensor):
        x = x.detach().cpu().numpy()
    a = np.asarray(x, dtype=dtype)
    assert a.shape == tuple(shape), (a.shape, shape)
    inputs.append(Tensor.from_numpy(
        np.ascontiguousarray(a)).to(device))

for x in data["task_in"]:
    add(x, np.int64, (1,))
for key in ("ihq_in", "jet_name_in", "jet_status_in"):
    add(data[key], np.int64, (1,50))
for x in data["deep_in"]:
    add(x, np.int64, (1,))
wide = np.stack([x.numpy() for x in data["wide_in"]], axis=1)
add(wide, np.float32, (1,127))
add(data["input_ids"], np.int64, (1,5))
add(data["attention_mask"], np.int64, (1,5))
for key in ("page_in", "item_in", "item_meta_in"):
    add(data[key], np.int64, (1,50))
add(data["page_meta_wide_in"][0].numpy()[:,:,None],
    np.float32, (1,50,1))

inv = np.load(
    base/"sequence_weights/fn_rotary_emb_inv_freq.npy"
).astype(np.float32)
freq = np.arange(50,dtype=np.float32)[:,None] * inv[None,:]
pos = np.concatenate([freq,freq],axis=-1)[None,None,:,:]
add(pos,np.float32,(1,1,50,256))

for i in range(10):
    for j in range(3):
        add(data["sibling_deep_in"][:,j,i],np.int64,(1,))
    add(data["sibling_wide_in"][:,:,i],np.float32,(1,18))
assert len(inputs) == 70

graph = ns[
    "build_grecbase_fusion_graph_sibling_fixed"
](DeviceRef.CPU())
model = InferenceSession(devices=[device]).load(
    graph, weights_registry=weights
)
actual = model.execute(*inputs)[0].to_numpy()
assert actual.shape == (1,8,256), actual.shape

ref = np.load(base/"real_sanity_pytorch_branches.npz")
labels = ["Sequence","Context","Search0","Search1",
          "JET","IHQ","Sibling","Task"]
keys = ["sequence","context","search0","search1",
        "task","jet","ihq","sibling"]

print("\n=== UPDATED REAL BRANCH PARITY ===")
for i, (label,key) in enumerate(zip(labels,keys)):
    a = ref[key]
    b = actual[:,i,:]
    diff = np.abs(a.astype(np.float64)-b.astype(np.float64))
    match = np.allclose(a,b,rtol=1e-3,atol=1e-3)
    print(f"{label:<9} mean={diff.mean():.6f} "
          f"max={diff.max():.6f} match={bool(match)}")

np.savez(base/"real_sanity_max_branches_sibling_fixed.npz",
         **{name:actual[:,i,:]
            for i,name in enumerate(labels)})

print("\nSIBLING CORRECTION TEST COMPLETE")
print("ORIGINAL DS AND PREVIOUS MAX FILES UNCHANGED")
PY
