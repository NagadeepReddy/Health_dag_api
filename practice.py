ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

ROOT="$ROOT" python3 - <<'PY'
import ast
import os
from pathlib import Path

root = Path(os.environ["ROOT"])
entry = root / "grecbase_fusion_full_head_72_max.py"
tree = ast.parse(entry.read_text())

modules = set()
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module:
        modules.add(node.module.split(".")[-1])

print("=== BPLAN BATCH-2 GRAPH DEPENDENCIES ===")
for module in sorted(modules):
    path = root / (module + ".py")
    if not path.exists():
        continue
    print(f"\n=== {path.name} ===")
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if any(term in line for term in (
            "reshape(", "TensorType(", "range(1)",
            "shape[0]", "[1,", "(1,", "batch_size",
            "valid_length", "squeeze(", "unsqueeze("
        )):
            print(f"{number}: {line.strip()[:150]}")

print("\nBPLAN BATCH-2 DEPENDENCY INSPECTION COMPLETE")
PY
