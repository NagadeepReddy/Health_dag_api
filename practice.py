cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path("artifacts/v1.472-max/pzaas_max")

print("=== PZAAS SEQUENCE + CONTEXT IMPLEMENTATION ===")

p = root / "main_context_max.py"
lines = p.read_text().splitlines()

print("\n=== CONTEXT FORWARD ===")
for i in range(9, min(68, len(lines))):
    print(f"{i+1}: {lines[i]}")

p = root / "grecbase_fusion_full_head_72_max.py"
lines = p.read_text().splitlines()

print("\n=== SEQUENCE GRAPH ===")
for i in range(16, min(41, len(lines))):
    print(f"{i+1}: {lines[i]}")

print("\n=== SEQUENCE COMPONENT DEFINITIONS ===")
for p in sorted(root.glob("*.py")):
    tree = ast.parse(p.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if any(x in node.name.lower() for x in (
                "postprocess", "features", "sequence"
            )):
                print(p.name, node.name,
                      node.lineno, node.end_lineno)

print("\nSEQUENCE / CONTEXT SOURCE: COMPLETE")
print("ORIGINAL DS: UNCHANGED")
print("NEXT: REAL MAX PARITY")
PY
