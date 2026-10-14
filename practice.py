python3 - <<'PY'
from pathlib import Path
import ast, shutil

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
src = p.read_text()
tree = ast.parse(src)
matches = []

def target(n, name):
    return (isinstance(n, ast.Assign)
            and len(n.targets) == 1
            and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id == name)

for parent in ast.walk(tree):
    body = getattr(parent, "body", [])
    if not isinstance(body, list):
        continue
    for a, b in zip(body, body[1:]):
        if not (target(a, "causal") and target(b, "scores")):
            continue
        if not (isinstance(a.value, ast.Call)
                and isinstance(a.value.func, ast.Attribute)
                and a.value.func.attr == "triu"):
            continue
        if not (isinstance(b.value, ast.BinOp)
                and isinstance(b.value.op, ast.Add)
                and isinstance(b.value.left, ast.Name)
                and b.value.left.id == "scores"
                and any(isinstance(n, ast.Name) and n.id == "causal"
                        for n in ast.walk(b.value))):
            continue
        matches.append((a, b))

assert len(matches) == 1, f"STOP: Found {len(matches)} matching blocks. No changes."

a, b = matches[0]
lines = src.splitlines(keepends=True)
updated = "".join(lines[:a.lineno-1] + lines[b.end_lineno:])
ast.parse(updated)

backup = p.with_suffix(".py.before_causal_removal.bak")
shutil.copy2(p, backup)
p.write_text(updated)

print("MAX causal mask removed")
print("Python syntax PASS")
print("Original DS code UNCHANGED")
print("Backup:", backup)
PY
