python3 - <<'PY'
import ast
from pathlib import Path

root = Path("../cta-max-release-review/artifacts/v1.168-max/cta_max")
files = {p.stem: p for p in root.glob("*.py")}
deps = {}

for name, path in files.items():
    tree = ast.parse(path.read_text())
    refs = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            refs.update(a.name.split(".")[-1] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                refs.add(node.module.split(".")[-1])
            refs.update(a.name for a in node.names)
    deps[name] = refs & files.keys()

used = set()
def visit(name):
    if name in used or name not in files:
        return
    used.add(name)
    for dep in deps[name]:
        visit(dep)

for entry in ["serve_max", "live_cta_pipeline_bridge"]:
    visit(entry)

print("RELEASE FILES:", len(files))
print("STATICALLY REFERENCED:", len(used))
print("\nFILES REQUIRING REVIEW:")
for name in sorted(files.keys() - used):
    print(" -", files[name].name)

print("\nNO FILES CHANGED OR DELETED")
PY
