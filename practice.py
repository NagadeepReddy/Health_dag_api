python - <<'PY'
import ast
from pathlib import Path

files = [
    ("artifacts/v1.168/Model.py",
     ("__init__", "predict_raw")),
    ("artifacts/v1.168/core-artifact/pipeline.py",
     ("load",)),
]

for filename, names in files:
    p = Path(filename)
    source = p.read_text()
    lines = source.splitlines()
    tree = ast.parse(source)

    print(f"\n===== {p.name} =====")

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name not in names:
            continue

        print(f"\nMETHOD: {node.name}")
        print("ARGS:", ast.unparse(node.args))
        print("LINES:", node.lineno, "-", node.end_lineno)

        limit = 45 if node.name == "load" else 35

        for n in range(
            node.lineno,
            min(node.end_lineno, node.lineno + limit - 1) + 1
        ):
            print(f"{n}: {lines[n-1]}")

        if node.end_lineno >= node.lineno + limit:
            print("... remaining implementation omitted")

print("\n===== REAL TEST FILES =====")
root = Path("artifacts/v1.168")
for p in sorted(root.rglob("sanity_input.json"))[:3]:
    print("INPUT:", p)

print("\nREAD ONLY — NO FILES MODIFIED")
PY
