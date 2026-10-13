cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_input_adapter.py")
src = p.read_text()

old_def = "def build_real_inputs():"
assert src.count(old_def) == 1, "STOP: Unexpected function signature"

tree = ast.parse(src)
fn = next(
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_real_inputs"
)

calls = [
    n for n in ast.walk(fn)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Attribute)
    and isinstance(n.func.value, ast.Name)
    and n.func.value.id == "torch"
    and n.func.attr == "load"
]

assert len(calls) == 1, "STOP: Unexpected saved-input loader"

node = calls[0]
lines = src.splitlines(keepends=True)

start = sum(map(len, lines[:node.lineno - 1])) + node.col_offset
end = sum(map(len, lines[:node.end_lineno - 1])) + node.end_col_offset

original = src[start:end]

updated = (
    src[:start]
    + "(model_in if model_in is not None else " + original + ")"
    + src[end:]
)

updated = updated.replace(
    old_def,
    "def build_real_inputs(model_in=None):",
    1
)

ast.parse(updated)

backup = p.with_name(p.name + ".before_live_input_support")
assert not backup.exists(), "STOP: Backup already exists"

shutil.copy2(p, backup)
p.write_text(updated)

print("LIVE INPUT SUPPORT: READY")
print("SAVED INPUT BEHAVIOR: PRESERVED")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS/PIPELINE: UNCHANGED")
PY
