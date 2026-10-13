python - <<'PY'
import ast
import os
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/main_context_max.py")
backup = p.with_name("main_context_max.py.before_activation_fix.bak")

assert p.is_file()
original = p.read_text()
tree = ast.parse(original)

funcs = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "main_context_forward"
]
assert len(funcs) == 1, "Unexpected function structure"

found = {}

for stmt in funcs[0].body:
    if not isinstance(stmt, ast.Assign):
        continue
    if len(stmt.targets) != 1:
        continue
    if not isinstance(stmt.targets[0], ast.Name):
        continue

    name = stmt.targets[0].id
    expr = ast.unparse(stmt.value)

    if (
        name in ("deep", "wide")
        and f"ops.relu({name})" in expr
        and f"ops.relu(-{name})" in expr
    ):
        assert name not in found
        found[name] = (stmt.lineno, stmt.end_lineno)

assert set(found) == {"deep", "wide"}, (
    "Expected exactly two extra activations; no edits made",
    found
)

lines = original.splitlines(keepends=True)
remove = set()

for start, end in found.values():
    remove.update(range(start, end + 1))

updated = "".join(
    line for i, line in enumerate(lines, 1)
    if i not in remove
)

compile(updated, str(p), "exec")

if backup.exists():
    assert backup.read_text() == original, (
        "Existing backup differs; refusing overwrite"
    )
else:
    backup.write_text(original)

tmp = p.with_name("main_context_max.py.activation_tmp")
assert not tmp.exists()

try:
    tmp.write_text(updated)
    os.replace(tmp, p)
finally:
    if tmp.exists():
        tmp.unlink()

assert p.read_text() == updated

print("MAIN CONTEXT EXTRA ACTIVATIONS: REMOVED")
print("DEEP + WIDE: CORRECTED")
print("MAX SOURCE SYNTAX: PASS")
print("BACKUP:", backup)
print("ORIGINAL PYTORCH AND DS CODE: UNCHANGED")
PY
