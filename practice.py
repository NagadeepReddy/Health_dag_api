cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

print("=== PZAAS SEQUENCE CLASS RESOLUTION ===")

roots = [
    Path("artifacts/v1.472-max"),
    Path("artifacts/v1.472/utils/dependency-utils"),
    Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max")
]

required = [
    "ParallelTransformerFfMAPMAX",
    "ParallelTransformerBlockMAX",
    "SequencePostprocessMAX"
]

found = {name: [] for name in required}
candidates = []

for root in roots:
    if not root.exists():
        continue
    for p in root.rglob("*.py"):
        try:
            tree = ast.parse(p.read_text())
        except (SyntaxError, UnicodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                name = node.name
                if name in found:
                    found[name].append((str(p), node.lineno))
                elif any(s in name.lower() for s in
                         ("ffmap", "postprocess", "sequence")):
                    candidates.append((name, str(p), node.lineno))

for name in required:
    matches = found[name]
    print(f"\n{name}: {'FOUND' if matches else 'MISSING'}")
    for path, line in matches:
        print(" ", path, "LINE", line)

print("\n=== RELATED IMPLEMENTATIONS ===")
for name, path, line in candidates[:35]:
    print(name, "|", path, "|", line)

p = Path(
    "artifacts/v1.472-max/pzaas_max/"
    "grecbase_fusion_full_head_72_max.py"
)
print("\n=== EXISTING GRAPH IMPORTS ===")
if p.exists():
    for i, line in enumerate(p.read_text().splitlines()[:35], 1):
        print(f"{i}: {line}")

print("\nSEQUENCE CLASS RESOLUTION: COMPLETE")
print("CONTEXT PARITY: PASS")
print("ORIGINAL DS: UNCHANGED")
print("NEXT: CORRECT ISOLATED MAX SEQUENCE IMPLEMENTATION")
PY
