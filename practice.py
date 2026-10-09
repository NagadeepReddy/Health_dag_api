python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_transformer_max.py")
s = p.read_text()

old = '''weights[name] = WeightData(
        name,
        arr,
        dtype=DType.float32,
        shape=Shape(arr.shape),
    )'''

new = '''weights[name] = WeightData(
        arr,
        name=name,
        dtype=DType.float32,
        shape=Shape(arr.shape),
    )'''

if old not in s:
    raise SystemExit("TARGET BLOCK NOT FOUND - NO CHANGE MADE")

s = s.replace(old, new)
p.write_text(s)

compile(s, str(p), "exec")
print("TRANSFORMER WEIGHTDATA ORDER FIXED")
print("RUNNER SYNTAX CLEAN")
PY
