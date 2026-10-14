cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path
import ast, shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_input_adapter.py")
s = p.read_text()

tree = ast.parse(s)
functions = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_real_inputs"
]
assert len(functions) == 1, "STOP: Unexpected adapter"
fn = functions[0]

if any(a.arg == "model_in" for a in fn.args.args):
    print("LIVE INPUT SUPPORT ALREADY EXISTS")
    print("NO FILES MODIFIED")
    raise SystemExit(0)

old_def = "def build_real_inputs():"
old_load = 'x = torch.load(p, map_location="cpu", weights_only=False)'

assert s.count(old_def) == 1, "STOP: Signature differs"
assert s.count(old_load) == 1, "STOP: Loader differs"

updated = s.replace(
    old_def,
    "def build_real_inputs(model_in=None):",
    1
).replace(
    old_load,
    "x = model_in if model_in is not None else torch.load(p, map_location='cpu', weights_only=False)",
    1
)

ast.parse(updated)

backup = p.with_name(p.name + ".before_live_input_support")
assert not backup.exists(), "STOP: Backup already exists"

shutil.copy2(p, backup)
p.write_text(updated)

print("LIVE INPUT SUPPORT: READY")
print("EXISTING SAVED INPUT: PRESERVED")
print("BACKUP: CREATED")
print("PYTHON SYNTAX: PASS")
print("DS AND PIPELINE: UNCHANGED")
PY
