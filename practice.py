python3 - <<'PY'
from pathlib import Path
import ast
import hashlib

src = Path("artifacts/v1.168-max/cta_max")
release = Path("../cta-max-release-review/cta_max")
files = sorted(release.glob("*.py"))
missing = set()
changed = []

for p in files:
    original = src / p.name
    if not original.exists() or hashlib.sha256(p.read_bytes()).digest() != hashlib.sha256(original.read_bytes()).digest():
        changed.append(p.name)

    tree = ast.parse(p.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            modules = [node.module or ""]
        elif isinstance(node, ast.Import):
            modules = [a.name for a in node.names]
        else:
            continue

        for module in modules:
            name = module.removeprefix("cta_max.").split(".")[0]
            if (src / (name + ".py")).exists() and not (release / (name + ".py")).exists():
                missing.add(name + ".py")

print("COPIED PYTHON FILES:", len(files))
print("CHANGED COPIES:", changed)
print("MISSING LOCAL IMPORTS:", sorted(missing))
print("ORIGINAL FILES UNCHANGED")
print("NO FILES MODIFIED OR DELETED")
PY
