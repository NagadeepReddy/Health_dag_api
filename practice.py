python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

files = [
    "grecbase_fusion_parity_max.py",
    "grecbase_fusion_order_correct_max.py",
    "grecbase_fusion_real_shapes_max.py",
    "parallel_transformer_graph_full_sequence.py",
]

for name in files:
    p = base / name
    if not p.exists():
        continue

    print("\n===", name, "===")
    lines = p.read_text().splitlines()
    tree = ast.parse(p.read_text())

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        call = ast.unparse(node.func)

        if call in ("features", "feature", "seq_features"):
            print("LINE:", node.lineno)
            print("CALL:", ast.unparse(node)[:500])

    for i, line in enumerate(lines, 1):
        if "vl_in" in line or "vl_input" in line:
            print(f"VL LINE {i}: {line.strip()[:180]}")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
