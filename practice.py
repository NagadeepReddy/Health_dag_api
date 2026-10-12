python - <<'PY'
import ast
from pathlib import Path

p = Path(
    "artifacts/v1.168-max/cta_max/"
    "grecbase_aux_features_max.py"
)

source = p.read_text()
tree = ast.parse(source)
lines = source.splitlines()

print("=== AUXILIARY BRANCH IMPLEMENTATION ===")

for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        print("\nFUNCTION:", node.name)
        print("ARGS:", ast.unparse(node.args))

        if node.name == "grecbase_aux_features":
            for i in range(node.lineno, node.end_lineno + 1):
                print(f"{i}: {lines[i-1]}")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
