python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_transformer_max.py")
s = p.read_text()

# Add Shape import once.
if "from max.graph import Shape" not in s:
    s = s.replace(
        "from max.graph import DeviceRef\n",
        "from max.graph import DeviceRef, Shape\n"
    )

start = s.index('weights["weight"] = WeightData(')
end = s.index('\n\nmodel = session.load', start)

new = '''norm1_arr = np.load(next(
    Path("artifacts/v1.168-max/cta_max/sequence_weights").glob("*norm1*g*.npy")
))
weights["weight"] = WeightData(
    norm1_arr,
    dtype=DType.float32,
    shape=Shape(norm1_arr.shape),
    name="weight",
)'''

s = s[:start] + new + s[end:]
p.write_text(s)

print("NORM1 WEIGHTDATA CONSTRUCTION CORRECTED")
PY

python -m py_compile artifacts/v1.168-max/cta_max/run_transformer_max.py && \
echo "RUNNER SYNTAX CLEAN"
