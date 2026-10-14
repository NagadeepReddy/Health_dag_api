cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_input_adapter.py")
s = p.read_text()
tree = ast.parse(s)
lines = s.splitlines(keepends=True)

def one(nodes, name):
    assert len(nodes) == 1, f"STOP: Unexpected {name}"
    return nodes[0]

loader = one([
    n for n in tree.body
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "data" for t in n.targets)
], "loader")

check = one([
    n for n in tree.body
    if isinstance(n, ast.Assert)
    and "isinstance(data, dict)" in ast.unparse(n.test)
], "dictionary check")

getter = one([
    n for n in tree.body
    if isinstance(n, ast.FunctionDef) and n.name == "get"
], "getter")

build = one([
    n for n in tree.body
    if isinstance(n, ast.FunctionDef) and n.name == "build_real_inputs"
], "adapter")

assert "torch.load" in ast.unparse(loader.value)
assert check.lineno == loader.end_lineno + 1
assert not build.args.args
assert lines[build.lineno - 1].strip() == "def build_real_inputs():"

getter_text = "".join(
    "    " + line if line.strip() else line
    for line in lines[getter.lineno - 1:getter.end_lineno]
)

new_header = (
    "def build_real_inputs(model_in=None):\n"
    "    data = model_in if model_in is not None else "
    'torch.load(SOURCE, map_location="cpu", weights_only=True)\n'
    '    assert isinstance(data, dict), "Expected input dictionary"\n'
    "\n"
    + getter_text + "\n"
)

edits = [
    (loader.lineno - 1, check.end_lineno, ""),
    (getter.lineno - 1, getter.end_lineno, ""),
    (build.lineno - 1, build.lineno, new_header),
]

for a, b, replacement in sorted(edits, reverse=True):
    lines[a:b] = [replacement]

updated = "".join(lines)
ast.parse(updated)

backup = p.with_name(p.name + ".before_live_input_support")
assert not backup.exists(), "STOP: Backup already exists"

shutil.copy2(p, backup)
p.write_text(updated)

print("LIVE INPUT SUPPORT: READY")
print("SAVED INPUT FALLBACK: PRESERVED")
print("72-INPUT MAPPING: UNCHANGED")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS/PIPELINE: UNCHANGED")
PY
