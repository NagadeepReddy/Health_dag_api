podman run --rm -i -v "$PWD:/workspace" -w /workspace --entrypoint python docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

base = Path("artifacts/v1.168-max/cta_max")
checkpoint = Path("artifacts/v1.168/core-artifact/model_0_base.pt")

pt_path = base / "real_sanity_pytorch_output.npy"
max_path = base / "real_sanity_max_output.npy"

weights = torch.load(checkpoint, map_location="cpu", weights_only=True)
if isinstance(weights, dict) and "state_dict" in weights:
    weights = weights["state_dict"]

required = [
    "remove_tasks_dense1.weight",
    "remove_tasks_dense1.bias",
    "remove_tasks_act1.w1.weight",
    "remove_tasks_act1.w2.weight",
    "remove_tasks_act1.w3.weight",
    "remove_tasks_dense2.weight",
]

missing = [k for k in required if k not in weights]
if missing:
    raise SystemExit(f"MISSING CHECKPOINT WEIGHTS: {missing}")

x = torch.from_numpy(np.load(pt_path).astype(np.float32))
mx = np.load(max_path)

print("SAVED PYTORCH TENSOR:", tuple(x.shape))
print("SAVED MAX FINAL:", mx.shape)

if tuple(x.shape) != (1, 2048) or mx.shape != (1, 10819):
    raise SystemExit("UNEXPECTED SHAPES - STOP WITHOUT CHANGES")

def linear(value, name, bias=False):
    w = weights[name + ".weight"].float()
    b = weights[name + ".bias"].float() if bias else None
    return F.linear(value, w, b)

with torch.no_grad():
    x = linear(x, "remove_tasks_dense1", bias=True)
    a = linear(x, "remove_tasks_act1.w1")
    b = linear(x, "remove_tasks_act1.w3")
    h = linear(F.silu(a) * b, "remove_tasks_act1.w2")
    ref = linear(h, "remove_tasks_dense2").numpy()

assert ref.shape == mx.shape == (1, 10819)

diff = np.abs(ref.astype(np.float64) - mx.astype(np.float64))
match = np.allclose(ref, mx, rtol=1e-3, atol=1e-3)

print("\n=== TRAINED FINAL-LAYER COMPARISON ===")
print("PYTORCH FINAL SHAPE:", ref.shape)
print("MAX FINAL SHAPE:", mx.shape)
print("MAX DIFFERENCE:", float(diff.max()))
print("MEAN DIFFERENCE:", float(diff.mean()))
print("MATCH:", bool(match))

output = base / "real_sanity_pytorch_final_from_2048_candidate.npy"
if output.exists():
    print("CANDIDATE ALREADY EXISTS - NOT OVERWRITING:", output)
else:
    np.save(output, ref)
    print("CANDIDATE REFERENCE SAVED:", output)

print("NOTE: Confirm saved 2048 tensor is the original get_path input")
print("ORIGINAL PYTORCH AND DS SOURCE UNCHANGED")
PY
