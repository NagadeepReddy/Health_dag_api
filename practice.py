python3 - <<'PY'
import ast
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/pipeline.py")
lines = p.read_text().splitlines()
tree = ast.parse("\n".join(lines))

found = False
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "inference_router":
        found = True
        print(f"=== ORIGINAL DS inference_router: lines {node.lineno}-{node.end_lineno} ===")
        for i in range(node.lineno, node.end_lineno + 1):
            s = lines[i-1]
            if any(x in s.lower() for x in (
                "sourcesystem", "networktype", "devicecategory",
                "ctalist", "propositionlist", "return ",
                "if ", "elif ", "else:", "router"
            )):
                print(f"{i}: {s[:220]}")
        break

if not found:
    print("Router method not in pipeline.py; searching original DS files...")
    root = p.parent
    for f in root.rglob("*.py"):
        if f == p or ".ipynb_checkpoints" in str(f):
            continue
        for i, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
            if "def inference_router(" in line:
                print(f"{f}:{i}: {line.strip()}")
                found = True

print("ROUTER FOUND:", found)
print("ORIGINAL DS UNCHANGED")
PY
