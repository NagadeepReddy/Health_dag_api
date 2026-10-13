python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")

names = [
    "grecbase_fusion_order_correct_max.py",
    "main_context_max.py",
    "sibling_context_max.py",
    "grecbase_aux_branches_max.py",
    "att_pooling_max.py",
    "grecbase_get_path_reference_max.py",
]

print("=== COMBINED MAX IMPLEMENTATION REVIEW ===")

for name in names:
    p = base / name
    print(f"\n========== {name} ==========")

    if not p.exists():
        print("NOT FOUND")
        continue

    lines = p.read_text().splitlines()
    tree = ast.parse("\n".join(lines))

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            print(f"\nFUNCTION {node.name}")
            for line in lines[node.lineno-1:min(node.end_lineno, node.lineno+65)]:
                print(line[:170])

        elif isinstance(node, ast.ClassDef):
            print(f"\nCLASS {node.name}")
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name in (
                    "__call__", "forward"
                ):
                    print(f"METHOD {child.name}")
                    for line in lines[
                        child.lineno-1:min(child.end_lineno, child.lineno+45)
                    ]:
                        print(line[:170])

print("\n=== GRAPH USAGE ===")
for p in sorted(base.glob("*.py")):
    if p.name in names:
        continue
    source = p.read_text(errors="replace")
    for target in (
        "grecbase_fusion_order_correct_max",
        "real_sanity_max_branches",
    ):
        if target in source:
            print(p.name, "uses", target)

print("\nREAD ONLY — NOTHING MODIFIED")
PY
