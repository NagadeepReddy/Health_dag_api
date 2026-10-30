POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-importfirst-8766-10g

"${POD[@]}" exec -i -e PYTHONDONTWRITEBYTECODE=1 "$NAME" \
  /opt/venv/bin/python -B - <<'PY'
from pathlib import Path
import ast

roots = [
    Path("/batch2/cta_max"),
    Path("/workspace/artifacts/v1.168-max/cta_max")
]

print("=== GET_PATH IMPLEMENTATION ===")

found = False
for root in roots:
    if not root.is_dir():
        continue

    for p in root.glob("*.py"):
        try:
            source = p.read_text()
            tree = ast.parse(source)
        except Exception:
            continue

        lines = source.splitlines()

        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if "get_path" not in node.name:
                continue

            found = True
            print(f"\nFILE: {p}")
            print(f"FUNCTION: {node.name}")
            print(f"LINES: {node.lineno}-{node.end_lineno}")

            for i in range(node.lineno, min(node.end_lineno, node.lineno + 150) + 1):
                print(f"{i:4}: {lines[i-1]}")

print("GET_PATH FOUND:", found)

print("\n=== ACTIVE GRAPH CALL SITE ===")
p = Path("/batch2/cta_max/grecbase_fusion_batch2_draft.py")

if p.is_file():
    lines = p.read_text().splitlines()
    for i, line in enumerate(lines, 1):
        if "grecbase_get_path_max(" in line:
            for j in range(max(1, i-5), min(len(lines), i+5)+1):
                print(f"{j:4}: {lines[j-1]}")

print("\nORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
