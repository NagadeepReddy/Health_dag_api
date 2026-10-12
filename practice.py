podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast
import sys
from pathlib import Path
import numpy as np

root = Path("/workspace/artifacts/v1.168-max")
base = root / "cta_max"
sys.path.insert(0, str(root))

source = base / "grecbase_fusion_parity_max.py"
target = base / "grecbase_fusion_wiring_fixed_max.py"

assert source.is_file()
tree = ast.parse(source.read_text())

builders = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_grecbase_fusion_graph_parity"
]
assert len(builders) == 1
fn = builders[0]

# Find the eight branch tensors joined before moe_norm1.
candidates = []
for n in ast.walk(fn):
    if not isinstance(n, ast.Assign):
        continue
    if not any(
        isinstance(t, ast.Name) and t.id == "outs"
        for t in n.targets
    ):
        continue

    v = n.value
    if not (
        isinstance(v, ast.Call)
        and isinstance(v.func, ast.Attribute)
        and v.func.attr in ("concat", "stack")
        and v.args
        and isinstance(v.args[0], (ast.List, ast.Tuple))
        and len(v.args[0].elts) == 8
    ):
        continue
    candidates.append(v.args[0])

if len(candidates) != 1:
    print("Eight-branch concatenation not uniquely located.")
    print("Matching candidates:", len(candidates))
    print("NO FILES MODIFIED")
    raise SystemExit(1)

parts = candidates[0].elts

# Existing: sequence, context, search0, search1,
#           sibling, task, jet, ihq
# Correct:  sequence, context, search0, search1,
#           task, jet, ihq, sibling
order = [0, 1, 2, 3, 5, 6, 7, 4]
candidates[0].elts = [parts[i] for i in order]

fn.name = "build_grecbase_fusion_graph_wiring_fixed"

updated = ast.unparse(
    ast.fix_missing_locations(tree)
) + "\n"

code = compile(updated, str(target), "exec")

namespace = {
    "__file__": str(target),
    "__name__": "cta_max.wiring_validation",
    "__package__": "cta_max",
}
exec(code, namespace)

from max.graph import DeviceRef

graph = namespace[
    "build_grecbase_fusion_graph_wiring_fixed"
](DeviceRef.CPU())

print("CORRECTED GRAPH CONSTRUCTION: PASS")

if target.exists():
    assert target.read_text() == updated, (
        "Target differs; refusing overwrite"
    )
else:
    target.write_text(updated)

print("CORRECTED GRAPH SAVED:", target)

# Reuse already captured real-input branch values.
pt = np.load(base / "real_sanity_pytorch_branches.npz")
mx = np.load(base / "real_sanity_max_branches.npz")

names = [
    "sequence", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
]

print("\n=== CORRECTED BRANCH COMPARISON ===")
print(f"{'BRANCH':<12} {'MEAN DIFF':>12} {'MAX DIFF':>12} {'MATCH':>7}")

corrected = {}
for i, name in enumerate(names):
    original_name = names[order[i]]
    actual = mx[original_name]
    expected = pt[name]
    assert actual.shape == expected.shape == (1, 256)

    diff = np.abs(
        actual.astype(np.float64)
        - expected.astype(np.float64)
    )
    match = np.allclose(
        actual, expected, rtol=1e-3, atol=1e-3
    )

    corrected[name] = actual
    print(
        f"{name:<12} {diff.mean():>12.6f} "
        f"{diff.max():>12.6f} {str(bool(match)):>7}"
    )

out = base / "real_sanity_max_branches_wiring_fixed.npz"
np.savez(out, **corrected)

print("\nCORRECTED BRANCH COMPARISON SAVED")
print("ORIGINAL WORKING MAX GRAPH UNCHANGED")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
