cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
p = ast.parse(Path("artifacts/v1.168/core-artifact/pipeline.py").read_text())
a = ast.parse((base / "run_real_sanity_input_adapter.py").read_text())

assignments = [
    n for n in ast.walk(p)
    if isinstance(n, ast.Assign)
    and isinstance(n.value, ast.Dict)
    and any(isinstance(t, ast.Name) and t.id == "model_in" for t in n.targets)
]
assert len(assignments) == 1, "STOP: Unexpected model_in definitions"

keys = {
    k.value for k in assignments[0].value.keys
    if isinstance(k, ast.Constant) and isinstance(k.value, str)
}

fn = next(n for n in ast.walk(a)
          if isinstance(n, ast.FunctionDef) and n.name == "build_real_inputs")

groups = [
    [v.value for v in n.args if isinstance(v, ast.Constant) and isinstance(v.value, str)]
    for n in ast.walk(fn)
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "get"
]

missing = [g for g in groups if g and not any(k in keys for k in g)]

print("PIPELINE INPUT KEYS:", len(keys))
print("ADAPTER INPUT LOOKUPS:", len(groups))
print("MISSING KEY GROUPS:", missing)
print("KEY CONTRACT:", "PASS" if not missing and groups else "NEEDS FIX")
print("NO FILES MODIFIED")
PY
