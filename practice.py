cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none \
-v /application1:/application1:ro \
-w /application1/sajjna8/rt-pzaas-v1.0 \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -c 'exec python3 -' <<'PY'
from pathlib import Path
import numpy as np
import torch

root = Path("artifacts/v1.472-max/pzaas_max/validation")
names = ["sequence", "context", "search0", "search1",
         "jet", "ihq", "sibling", "task"]

def tensor(x):
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().numpy()
    if isinstance(x, np.ndarray):
        return x
    return None

def load(name):
    return torch.load(
        root / name,
        map_location="cpu",
        weights_only=True
    )

print("=== PZAAS REFERENCE AND BRANCH TARGET ALIGNMENT ===")

reference = load("ppa_pytorch_reference_01.pt")
base = load("ppa_model_base_reference.pt")

assert isinstance(reference, dict)
assert "output" in reference

actual = tensor(reference["output"])
assert actual is not None

print("PYTORCH REFERENCE SHAPE:", actual.shape)
print("BASE REFERENCE TYPE:", type(base).__name__)

base_output = tensor(base)
if base_output is None and isinstance(base, dict):
    base_output = tensor(base.get("output"))

if base_output is not None:
    print("BASE REFERENCE SHAPE:", base_output.shape)
    if base_output.shape == actual.shape:
        diff = np.abs(base_output.astype(np.float64) -
                      actual.astype(np.float64))
        print("BASE VS PYTORCH MAX DIFF:", float(diff.max()))

with np.load(root / "pzaas_eight_branch_targets.npz",
             allow_pickle=False) as z:
    branches = [np.asarray(z[n], dtype=np.float32).reshape(-1)
                for n in names]

combined = np.concatenate(branches)

print("EIGHT-BRANCH CONCAT SHAPE:", combined.shape)
print("PYTORCH REFERENCE ELEMENTS:", actual.size)
print("BRANCH TARGET ELEMENTS:", combined.size)

if actual.size == combined.size:
    diff = np.abs(
        actual.astype(np.float64).reshape(-1) -
        combined.astype(np.float64)
    )
    print("REFERENCE VS TARGET MAX DIFF:", float(diff.max()))
    print("REFERENCE VS TARGET MEAN DIFF:", float(diff.mean()))
    print("REFERENCE AND TARGET CONSISTENCY:",
          "PASS" if np.allclose(actual.reshape(-1), combined,
                                atol=1e-6, rtol=1e-6)
          else "FAIL")
else:
    print("REFERENCE AND TARGET: DIFFERENT OUTPUT STAGES")
    print("DIRECT FULL-OUTPUT COMPARISON: INVALID")

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("FILES MODIFIED: NONE")
PY
