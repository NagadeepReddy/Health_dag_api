cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
source = p.read_text()
tree = ast.parse(source)

classes = [
    n for n in tree.body
    if isinstance(n, ast.ClassDef) and n.name == "GRecBase"
]
if len(classes) != 1:
    raise SystemExit("STOP: Original GRecBase not uniquely found")

print("=== ORIGINAL SEQUENCE INITIALIZATION ===")

for method in classes[0].body:
    if not isinstance(method, ast.FunctionDef):
        continue
    if method.name != "__init__":
        continue

    for node in ast.walk(method):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = (
                node.targets if isinstance(node, ast.Assign)
                else [node.target]
            )
            if any(
                "sequence_transformer" in ast.unparse(t)
                for t in targets
            ):
                print(
                    f"LINE {node.lineno}:",
                    ast.get_source_segment(source, node)
                )

print("\n=== ORIGINAL SEQUENCE CLASS REFERENCES ===")

for i, line in enumerate(source.splitlines(), 1):
    if (
        "ParallelTransformer" in line
        or "SequenceTransformer" in line
    ):
        print(f"{i}: {line}")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
