cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none \
-v /application1:/application1:ro \
-w /application1/sajjna8/rt-pzaas-v1.0 \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -c 'exec python3 -' <<'PY'
import numpy as np
import torch
from pathlib import Path
from itertools import permutations

root = Path("artifacts/v1.472-max/pzaas_max/validation")

names = [
    "sequence", "context", "search0", "search1",
    "jet", "ihq", "sibling", "task"
]

print("=== PZAAS EIGHT-BRANCH ALIGNMENT ===", flush=True)

ref = torch.load(
    root / "ppa_model_base_reference.pt",
    map_location="cpu",
    weights_only=True
)

if isinstance(ref, torch.Tensor):
    ref = ref.detach().cpu().numpy()
else:
    raise RuntimeError("Unexpected base reference structure")

assert ref.shape == (1, 2048)

reference = ref.reshape(8, 256).astype(np.float32)

with np.load(
    root / "pzaas_eight_branch_targets.npz",
    allow_pickle=False
) as z:
    assert all(n in z.files for n in names)
    saved = np.stack([
        np.asarray(z[n], dtype=np.float32).reshape(256)
        for n in names
    ])

cost = np.zeros((8, 8))
maximum = np.zeros((8, 8))

for i in range(8):
    for j in range(8):
        d = np.abs(saved[i] - reference[j])
        cost[i, j] = d.mean()
        maximum[i, j] = d.max()

identity = tuple(range(8))
best = min(
    permutations(range(8)),
    key=lambda p: sum(cost[i, p[i]] for i in range(8))
)

print("\n=== BEST BRANCH MATCHING ===")

for i, j in enumerate(best):
    print(
        f"{names[i]:9s} -> reference[{j}] "
        f"mean_diff={cost[i,j]:.8f} "
        f"max_diff={maximum[i,j]:.8f}"
    )

original_mae = sum(cost[i, i] for i in range(8)) / 8
matched_mae = sum(cost[i, best[i]] for i in range(8)) / 8

print("\n=== RESULTS ===")
print("ORIGINAL ORDER MEAN DIFF:", original_mae)
print("BEST ORDER MEAN DIFF:", matched_mae)
print("ORDER CHANGED:", best != identity)

same_order = all(
    np.allclose(saved[i], reference[i], rtol=1e-3, atol=1e-3)
    for i in range(8)
)

reordered = all(
    np.allclose(saved[i], reference[best[i]], rtol=1e-3, atol=1e-3)
    for i in range(8)
)

if same_order:
    print("BRANCH VALUE ALIGNMENT: PASS")
elif reordered:
    print("BRANCH VALUE ALIGNMENT: REORDERING CANDIDATE")
else:
    print("BRANCH VALUE ALIGNMENT: NUMERICAL DIFFERENCE REMAINS")

print("REFERENCE SAME-INPUT PROVENANCE: NOT YET VERIFIED")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("FILES MODIFIED: NONE")
PY
