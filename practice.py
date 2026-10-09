python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_context_head_deep.py")
s = p.read_text()

needle = 'session = InferenceSession(devices=[device])'

insert = '''
# MAX RMSNorm internally requests this registry key.
arr = np.load(weight_dir / "deep_norm.g.npy")
weights["weight"] = WeightData(
    arr,
    name="weight",
    dtype=DType.float32,
    shape=Shape(arr.shape),
)

'''

if 'weights["weight"] = WeightData' not in s:
    s = s.replace(needle, insert + needle)

p.write_text(s)
print("RMSNORM REGISTRY MAPPED")
PY
