python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
src = p.read_text()
tree = ast.parse(src)
matches = []

for fn in ast.walk(tree):
    if not isinstance(fn, ast.FunctionDef) or fn.name != "__call__":
        continue
    for a, b in zip(fn.body, fn.body[1:]):
        if not (isinstance(a, ast.Assign) and isinstance(b, ast.Assign)):
            continue
        if not (len(a.targets) == len(b.targets) == 1):
            continue
        if not (isinstance(a.targets[0], ast.Name) and a.targets[0].id == "causal"):
            continue
        if not (isinstance(b.targets[0], ast.Name) and b.targets[0].id == "scores"):
            continue
        if "np.triu" in ast.get_source_segment(src, a) and "ops.constant" in ast.get_source_segment(src, b):
            matches.append((a.lineno, b.end_lineno))

if len(matches) != 1:
    raise SystemExit(f"STOP: Expected one causal mask block, found {len(matches)}. No change.")

backup = p.with_suffix(".before_causal_alignment.bak")
if backup.exists():
    raise SystemExit("STOP: Backup already exists. No change.")

start, end = matches[0]
lines = src.splitlines(keepends=True)
updated = "".join(lines[:start-1] + lines[end:])
ast.parse(updated)

shutil.copy2(p, backup)
p.write_text(updated)

print("MAX extra causal mask REMOVED")
print("Python syntax PASS")
print("Original DS code UNCHANGED")
print("Backup:", backup)
PY
