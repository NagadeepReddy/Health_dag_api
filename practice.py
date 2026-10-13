podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast, sys
from pathlib import Path
import numpy as np

root = Path("/workspace/artifacts/v1.168-max")
base = root / "cta_max"
sys.path.insert(0, str(root))

source = base / "grecbase_fusion_parity_max.py"
target = base / "grecbase_fusion_order_correct_max.py"

tree = ast.parse(source.read_text())

fns = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_grecbase_fusion_graph_parity"
]
assert len(fns) == 1
fn = fns[0]

old_order = (
    "seq, context, search0, search1, "
    "task, jet, ihq, sibling"
)
new_order = (
    "seq, context, search0, search1, "
    "jet, ihq, sibling, task"
)

# Locate the exact original eight-branch comprehension.
matches = []
for n in ast.walk(fn):
    if isinstance(n, ast.ListComp):
        for g in n.generators:
            if (
                isinstance(g.iter, ast.Tuple)
                and ast.unparse(g.iter)[1:-1] == old_order
            ):
                matches.append(g)

assert len(matches) == 1, (
    "Unexpected branch wiring structure:",
    len(matches)
)

matches[0].iter = ast.parse(
    "(" + new_order + ")", mode="eval"
).body

fn.name = "build_grecbase_fusion_graph_order_correct"

updated = ast.unparse(
    ast.fix_missing_locations(tree)
) + "\n"

code = compile(updated, str(target), "exec")
ns = {
    "__file__": str(target),
    "__name__": "cta_max.order_check",
    "__package__": "cta_max"
}
exec(code, ns)

from max.graph import DeviceRef

graph = ns[
    "build_grecbase_fusion_graph_order_correct"
](DeviceRef.CPU())

print("CORRECTED MAX GRAPH CONSTRUCTION: PASS")

if target.exists():
    assert target.read_text() == updated, (
        "Existing target differs; not overwriting"
    )
else:
    target.write_text(updated)

print("CORRECTED MAX GRAPH SAVED:", target.name)

pt = np.load(base / "real_sanity_pytorch_branches.npz")
mx = np.load(base / "real_sanity_max_branches.npz")

# Previous PyTorch capture labels were assigned using
# the incorrect assumed order.
mapping = [
    ("sequence", "sequence", "Sequence"),
    ("context", "context", "Context"),
    ("search0", "search0", "Search0"),
    ("search1", "search1", "Search1"),
    ("task", "jet", "JET"),
    ("jet", "ihq", "IHQ"),
    ("ihq", "sibling", "Sibling"),
    ("sibling", "task", "Task")
]

print("\n=== CORRECTLY LABELED BRANCH PARITY ===")
for pt_key, mx_key, label in mapping:
    a, b = pt[pt_key], mx[mx_key]
    assert a.shape == b.shape == (1, 256)
    diff = np.abs(a.astype(np.float64) - b.astype(np.float64))
    match = np.allclose(a, b, rtol=1e-3, atol=1e-3)
    print(
        f"{label:<10} mean={diff.mean():.6f} "
        f"max={diff.max():.6f} match={bool(match)}"
    )

print("\nORIGINAL PYTORCH AND DS FILES UNCHANGED")
print("PREVIOUS WORKING MAX FILES UNCHANGED")
PY
