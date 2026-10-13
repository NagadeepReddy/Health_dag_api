python - <<'PY'
from pathlib import Path
import numpy as np

base = Path("artifacts/v1.168-max/cta_max")
weights = base / "grecbase_integration_weights"

names = [
    "remove_tasks_dense1.weight",
    "remove_tasks_dense1.bias",
    "remove_tasks_act1.w1.weight",
    "remove_tasks_act1.w3.weight",
    "remove_tasks_act1.w2.weight",
    "remove_tasks_dense2.weight",
]

files = {n: weights / (n + ".npy") for n in names}
missing = [n for n, p in files.items() if not p.is_file()]

input_file = base / "real_sanity_max_2048.npy"

print("=== FINAL GET_PATH ISOLATION ===")
print("INPUT FOUND:", input_file.is_file())
print("MISSING WEIGHTS:", missing)

if not input_file.is_file() or missing:
    print("STOP: Required saved inputs unavailable. Nothing changed.")
    raise SystemExit(0)

w = {n: np.load(p).astype(np.float32) for n, p in files.items()}
x = np.load(input_file).astype(np.float32)

assert x.shape == (1, 2048), x.shape

def linear(v, prefix, bias=False):
    result = v @ w[prefix + ".weight"].T
    if bias:
        result = result + w[prefix + ".bias"]
    return result

x = linear(x, "remove_tasks_dense1", True)
a = linear(x, "remove_tasks_act1.w1")
b = linear(x, "remove_tasks_act1.w3")

with np.errstate(over="ignore"):
    swish = a / (1.0 + np.exp(-a))

hidden = linear(swish * b, "remove_tasks_act1.w2")
calculated = linear(hidden, "remove_tasks_dense2")

print("CALCULATED SHAPE:", calculated.shape)
print("FINITE:", bool(np.isfinite(calculated).all()))

references = [
    "real_sanity_pytorch_final_from_2048_candidate.npy",
    "real_sanity_max_output.npy",
]

for name in references:
    p = base / name
    if not p.is_file():
        print(name, "NOT FOUND")
        continue

    ref = np.load(p)
    print("\nREFERENCE:", name)
    print("SHAPE:", ref.shape)

    if ref.shape == calculated.shape:
        diff = np.abs(calculated.astype(np.float64) - ref)
        print("MAX DIFF:", float(diff.max()))
        print("MEAN DIFF:", float(diff.mean()))
        print("MATCH:", bool(np.allclose(
            calculated, ref, rtol=1e-3, atol=1e-3
        )))

print("\nREAD ONLY — NO FILES MODIFIED")
PY
