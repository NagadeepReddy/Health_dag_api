python - <<'PY'
import ast
import os
from pathlib import Path

path = Path(
    "artifacts/v1.168-max/cta_max/sibling_context_max.py"
)
backup = path.with_name(
    "sibling_context_max.py.before_activation_fix.bak"
)

assert path.is_file(), f"Missing: {path}"
original = path.read_text()
tree = ast.parse(original)

functions = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "sibling_context_forward"
]
assert len(functions) == 1

remove = {}
for stmt in functions[0].body:
    if not isinstance(stmt, ast.Assign):
        continue
    if len(stmt.targets) != 1:
        continue
    if not isinstance(stmt.targets[0], ast.Name):
        continue

    name = stmt.targets[0].id
    expr = ast.unparse(stmt.value)

    if name in ("deep", "wide") and (
        f"ops.relu({name})" in expr
        and f"ops.relu(-{name})" in expr
    ):
        assert name not in remove
        remove[name] = (stmt.lineno, stmt.end_lineno)

assert set(remove) == {"deep", "wide"}, (
    "Expected two verified activations; refusing edit",
    remove
)

lines = original.splitlines(keepends=True)
deleted = set()

for start, end in remove.values():
    deleted.update(range(start, end + 1))

updated = "".join(
    line for number, line in enumerate(lines, 1)
    if number not in deleted
)

compile(updated, str(path), "exec")

# Confirm exactly those two assignments disappeared.
new_tree = ast.parse(updated)
new_fn = next(
    n for n in new_tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "sibling_context_forward"
)
assert not any(
    isinstance(s, ast.Assign)
    and len(s.targets) == 1
    and isinstance(s.targets[0], ast.Name)
    and s.targets[0].id in ("deep", "wide")
    and "ops.relu(" + s.targets[0].id + ")" in ast.unparse(s.value)
    for s in new_fn.body
)

if backup.exists():
    assert backup.read_text() == original, (
        "Backup already exists with different contents; stopped"
    )
else:
    backup.write_text(original)

temp = path.with_name("sibling_context_max.py.parity_tmp")
assert not temp.exists(), "Temporary file exists; stopped"

try:
    temp.write_text(updated)
    os.replace(temp, path)
finally:
    if temp.exists():
        temp.unlink()

assert path.read_text() == updated

print("SIBLING VERIFIED ACTIVATION FIX: SAVED")
print("DEEP AND WIDE EXTRA ACTIVATIONS: REMOVED")
print("MAX SOURCE SYNTAX: PASS")
print("BACKUP:", backup)
print("ORIGINAL PYTORCH AND DS CODE: UNCHANGED")

# Next targets, without changing them.
context = path.with_name("main_context_max.py")
sequence = path.with_name("parallel_transformer_graph_full_sequence.py")
print("MAIN CONTEXT FILE EXISTS:", context.is_file())
print("SEQUENCE GRAPH EXISTS:", sequence.is_file())
PY
