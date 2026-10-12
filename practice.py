python - <<'PY'
from pathlib import Path
import ast
import itertools
import numpy as np

base = Path("artifacts/v1.168-max/cta_max")
source = base / "grecbase_fusion_parity_max.py"

pt = np.load(base / "real_sanity_pytorch_branches.npz")
mx = np.load(base / "real_sanity_max_branches.npz")

names = [
    "sequence", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
]

# Identify the best one-to-one branch assignment.
cost = np.zeros((8, 8))
for i, a in enumerate(names):
    for j, b in enumerate(names):
        x = pt[a].astype(np.float64)
        y = mx[b].astype(np.float64)
        cost[i, j] = np.mean(np.abs(x - y))

best = min(
    itertools.permutations(range(8)),
    key=lambda p: sum(cost[i, p[i]] for i in range(8))
)

print("=== BEST ONE-TO-ONE BRANCH MATCH ===")
for i, j in enumerate(best):
    print(
        f"PyTorch {names[i]:<9} -> "
        f"MAX {names[j]:<9} "
        f"mean_diff={cost[i,j]:.6f}"
    )

print("\n=== ACTUAL MAX FUSION CODE ===")
lines = source.read_text().splitlines()
tree = ast.parse(source.read_text())

builders = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_grecbase_fusion_graph_parity"
]
assert len(builders) == 1

fn = builders[0]
hits = set()

for n in ast.walk(fn):
    if isinstance(n, ast.Call):
        expression = ast.unparse(n.func)
        if (
            expression.endswith(".concat")
            or expression.endswith(".stack")
            or (
                expression == "norm"
                and any(
                    isinstance(a, ast.Constant)
                    and a.value == "moe_norm1"
                    for a in n.args
                )
            )
        ):
            hits.add(n.lineno)

shown = set()
for line in sorted(hits):
    for i in range(max(fn.lineno, line-8),
                   min(fn.end_lineno, line+5)+1):
        if i not in shown:
            print(f"{i}: {lines[i-1]}")
            shown.add(i)
    print("---")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
