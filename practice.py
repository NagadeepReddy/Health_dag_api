cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none \
-v /application1:/application1:ro \
-w /application1/sajjna8/rt-pzaas-v1.0 \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -c 'exec python3 -' <<'PY'
import torch
import numpy as np
from pathlib import Path

root = Path("artifacts/v1.472-max/pzaas_max/validation")
names = [
    "sequence", "context", "search0", "search1",
    "jet", "ihq", "sibling", "task"
]

print("=== PZAAS PYTORCH OUTPUT STRUCTURE + PARITY DIAGNOSTIC ===", flush=True)

def inspect(obj, path="root", depth=0):
    if depth > 5:
        return

    if isinstance(obj, torch.Tensor):
        arr = obj.detach().cpu().numpy()
        print("TENSOR:", path, arr.shape, arr.dtype)
        if arr.size == 2048 and np.issubdtype(arr.dtype, np.number):
            candidates.append((path, arr.astype(np.float32).reshape(-1)))

    elif isinstance(obj, np.ndarray):
        print("ARRAY:", path, obj.shape, obj.dtype)
        if obj.size == 2048 and np.issubdtype(obj.dtype, np.number):
            candidates.append((path, obj.astype(np.float32).reshape(-1)))

    elif isinstance(obj, dict):
        print("DICT:", path, "KEYS:", list(obj.keys())[:25])
        for k, v in obj.items():
            inspect(v, path + "." + str(k), depth + 1)

    elif isinstance(obj, (list, tuple)):
        print("SEQUENCE:", path, "LENGTH:", len(obj))
        for i, v in enumerate(obj[:20]):
            inspect(v, path + "[" + str(i) + "]", depth + 1)

    else:
        print("OTHER:", path, type(obj).__name__)

candidates = []

for filename in [
    "ppa_pytorch_reference_01.pt",
    "ppa_model_base_reference.pt"
]:
    p = root / filename

    print("\nREFERENCE FILE:", filename)

    if not p.is_file():
        print("NOT FOUND")
        continue

    obj = torch.load(p, map_location="cpu", weights_only=True)
    inspect(obj, filename)

target = root / "pzaas_eight_branch_targets.npz"
assert target.is_file(), "Saved branch targets missing"

with np.load(target, allow_pickle=False) as z:
    assert all(n in z.files for n in names)
    branches = [
        np.asarray(z[n], dtype=np.float32).reshape(-1)
        for n in names
    ]

expected = np.concatenate(branches)
assert expected.shape == (2048,)

print("\n=== REFERENCE COMPARISON ===")
print("BRANCH CONCAT:", expected.shape)
print("2048-ELEMENT REFERENCE CANDIDATES:", len(candidates))

matched = False

for path, actual in candidates:
    diff = np.abs(actual - expected)
    passed = np.allclose(actual, expected, atol=1e-6, rtol=1e-6)

    print("CANDIDATE:", path)
    print("MAX DIFF:", float(diff.max()))
    print("MEAN DIFF:", float(diff.mean()))
    print("MATCH:", passed)

    matched |= passed

print("\n=== FINAL RESULTS ===")
print("PYTORCH REFERENCE STRUCTURE: INSPECTED")
print("EIGHT BRANCH TARGETS: VALID")
print("REFERENCE CONCAT MATCH:", "PASS" if matched else "NOT ESTABLISHED")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("FILES MODIFIED: NONE")
print("NEXT: VALIDATE SAME-STAGE BRANCH OUTPUTS")
PY
