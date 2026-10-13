cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
source = p.read_text()
tree = ast.parse(source)

for cls in ast.walk(tree):
    if isinstance(cls, ast.ClassDef) and cls.name == "GRecBase":
        for node in cls.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == "mm_pooling":
                    print("=== ORIGINAL mm_pooling ===")
                    print(ast.get_source_segment(source, node))

print("=== ORIGINAL SIBLING FORWARD LOGIC ===")
for i, line in enumerate(source.splitlines(), 1):
    if 1332 <= i <= 1338:
        print(f"{i}: {line}")
PY
