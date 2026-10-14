python3 - <<'PY'
from pathlib import Path
import ast, shutil

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
source = p.read_text()
tree = ast.parse(source)
matches = []

def assigns(node, name):
    return (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
    )

for parent in ast.walk(tree):
    body = getattr(parent, "body", None)
    if not isinstance(body, list):
        continue

    for i, node in enumerate(body):
        if not assigns(node, "causal"):
            continue
        if not any(
            isinstance(x, ast.Call)
            and isinstance(x.func, ast.Attribute)
            and x.func.attr == "triu"
            for x in ast.walk(node.value)
        ):
            continue

        additions = [
            later for later in body[i+1:]
            if assigns(later, "scores")
            and isinstance(later.value, ast.BinOp)
            and isinstance(later.value.op, ast.Add)
            and isinstance(later.value.left, ast.Name)
            and later.value.left.id == "scores"
            and any(
                isinstance(x, ast.Name) and x.id == "causal"
                for x in ast.walk(later.value)
            )
        ]
        if len(additions) == 1:
            matches.append((node, additions[0]))

assert len(matches) == 1, f"STOP: found {len(matches)} blocks; no changes"

a, b = matches[0]
lines = source.splitlines(keepends=True)

for node in sorted((a, b), key=lambda n: n.lineno, reverse=True):
    del lines[node.lineno-1:node.end_lineno]

updated = "".join(lines)
ast.parse(updated)

backup = p.with_suffix(".py.before_causal_removal.bak")
assert not backup.exists(), "STOP: backup exists; no changes"
shutil.copy2(p, backup)
p.write_text(updated)

print("MAX causal mask removed")
print("Python syntax PASS")
print("Original DS code UNCHANGED")
print("Backup:", backup)
PY
