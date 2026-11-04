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

root = Path("artifacts/v1.472-max/pzaas_max/validation")

names = [
    "sequence", "context", "search0", "search1",
    "jet", "ihq", "sibling", "task"
]

print("=== PZAAS PYTORCH REFERENCE ROOT-CAUSE CHECK ===", flush=True)

target_path = root / "pzaas_eight_branch_targets.npz"
assert target_path.is_file(), "Eight-branch targets missing"

with np.load(target_path, allow_pickle=False) as z:
    assert all(k in z.files for k in names)
    branches = {
        k: np.asarray(z[k], dtype=np.float32).reshape(-1)
        for k in names
    }

for name, value in branches.items():
    print(
        f"{name}: shape={value.shape}, "
        f"min={value.min():.6f}, "
        f"max={value.max():.6f}, "
        f"mean={value.mean():.6f}"
    )

expected = np.concatenate([branches[k] for k in names])
assert expected.size == 2048
assert np.isfinite(expected).all()

print("\nTARGET CONCATENATION: PASS")

def collect(obj, prefix="", depth=0):
    if depth > 5:
        return

    if isinstance(obj, torch.Tensor):
        a = obj.detach().cpu().numpy()
        if a.size in (256, 2048):
            yield prefix, np.asarray(a, dtype=np.float32).reshape(-1)

    elif isinstance(obj, np.ndarray):
        if obj.size in (256, 2048):
            yield prefix, np.asarray(obj, dtype=np.float32).reshape(-1)

    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from collect(v, prefix + "/" + str(k), depth + 1)

    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from collect(v, prefix + "/" + str(i), depth + 1)

reference_files = [
    "ppa_pytorch_reference_01.pt",
    "ppa_model_base_reference.pt"
]

matched = False
found_candidates = 0

for filename in reference_files:
    path = root / filename
    print("\nREFERENCE:", filename)

    if not path.is_file():
        print("STATUS: NOT FOUND")
        continue

    try:
        obj = torch.load(
            path,
            map_location="cpu",
            weights_only=True
        )
    except Exception as exc:
        print("CANNOT READ SAFELY:", str(exc)[:250])
        continue

    if isinstance(obj, dict):
        print("TOP-LEVEL KEYS:", list(obj)[:25])
    else:
        print("OBJECT TYPE:", type(obj).__name__)

    candidates = list(collect(obj))
    print("CANDIDATE TENSORS:", len(candidates))

    for key, value in candidates:
        if not np.isfinite(value).all():
            continue

        found_candidates += 1

        if value.size == 2048:
            diff = np.abs(value - expected)
            print(
                "FULL REFERENCE:", key,
                "max_diff=", float(diff.max()),
                "mean_diff=", float(diff.mean())
            )

            if np.allclose(value, expected, atol=1e-6, rtol=1e-6):
                matched = True
                print("SAVED TARGET REFERENCE: MATCH")

        elif value.size == 256:
            scores = sorted(
                (
                    float(np.max(np.abs(value - branches[k]))),
                    k
                )
                for k in names
            )
            best_diff, best_name = scores[0]
            if best_diff < 1e-3:
                print(
                    "BRANCH REFERENCE MATCH:",
                    key, "->", best_name,
                    "diff=", best_diff
                )
                matched = True

print("\n=== ROOT-CAUSE CHECK RESULTS ===")
print("PYTORCH TARGET ARRAY: VALID")
print("REFERENCE CANDIDATES:", found_candidates)

if matched:
    print("REFERENCE CONTENT CONSISTENCY: PASS")
    print("NEXT: VERIFY SAME-INPUT PROVENANCE AND MAX OPERATIONS")
else:
    print("REFERENCE CONTENT CONSISTENCY: NOT ESTABLISHED")
    print("NEXT: REGENERATE VERIFIED SAME-INPUT PYTORCH REFERENCE")

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("FILES MODIFIED: NONE")
PY
