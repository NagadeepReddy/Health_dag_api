python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_transformer_max.py")
s = p.read_text()

old = '''weights["weight"] = WeightData(
    np.load(next(
        Path("artifacts/v1.168-max/cta_max/sequence_weights").glob("*norm1*g*.npy")
    )),
    name="weight",
)'''

new = '''_norm1_arr = np.load(next(
    Path("artifacts/v1.168-max/cta_max/sequence_weights").glob("*norm1*g*.npy")
))
weights["weight"] = WeightData(
    _norm1_arr,
    dtype=DType.float32,
    shape=Shape(_norm1_arr.shape),
    name="weight",
)'''

if old not in s:
    raise SystemExit("TARGET BLOCK NOT FOUND - NO CHANGE MADE")

s = s.replace(old, new)
p.write_text(s)

print("TRANSFORMER NORM1 WEIGHTDATA FIXED")
PY

python -m py_compile artifacts/v1.168-max/cta_max/run_transformer_max.py && \
echo "RUNNER SYNTAX CLEAN"
