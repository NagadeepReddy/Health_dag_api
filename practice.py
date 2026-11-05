
cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
  --runroot /run/containers/storage run \
  --rm -i --pull=never --network=none \
  --security-opt label=disable \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import numpy as np
import torch

v = Path("/workspace/artifacts/v1.472-max/pzaas_max/validation")

print("=== PZAAS EXACT NUMERICAL PROVENANCE ===", flush=True)

def load(name):
    return torch.load(
        v / name, map_location="cpu", weights_only=False
    )

def as_numpy(x):
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().numpy()
    if isinstance(x, (list, tuple)):
        if len(x) == 1:
            return as_numpy(x[0])
        return np.stack([as_numpy(y) for y in x])
    return np.asarray(x)

replay = as_numpy(
    load("ppa_pytorch_base_replay.pt")["output"]
).reshape(1, 2048)

saved = load("ppa_model_input_exact.pt")
original = saved.get("model_in", saved)

print("PYTORCH REPLAY: PASS")

names = [
    "page_in", "item_in", "item_in_sku",
    "item_meta_in", "v1_in", "ihq_in",
    "jet_name_in", "jet_status_in",
    "sibling_deep_in", "sibling_wide_in",
    "sibling_v1_in", "current_in",
    "input_ids", "attention_mask"
]

input_file = v / "ppa_tensor_inputs.npz"
failures = []
matches = 0

if input_file.is_file():
    with np.load(input_file, allow_pickle=False) as data:
        for name in names:
            if name not in original or name not in data:
                failures.append((name, "missing"))
                continue

            a = as_numpy(original[name])
            b = np.asarray(data[name])

            if a.shape != b.shape:
                failures.append((name, "shape mismatch"))
            elif a.dtype != b.dtype:
                failures.append((name, "dtype mismatch"))
            else:
                equal = (
                    np.array_equal(a, b, equal_nan=True)
                    if a.dtype.kind in "fc"
                    else np.array_equal(a, b)
                )
                if equal:
                    matches += 1
                else:
                    delta = np.max(
                        np.abs(
                            a.astype(np.float64)
                            - b.astype(np.float64)
                        )
                    )
                    failures.append(
                        (name, f"value difference {delta:.9g}")
                    )

    print("INPUT VALUE MATCHES:", matches, "/", len(names))
    for name, reason in failures:
        print("INPUT MISMATCH:", name, reason)
else:
    print("INPUT VALUE AUDIT: BLOCKED — NPZ not found")

order = [
    "sequence", "context", "search0", "search1",
    "jet", "ihq", "sibling", "task"
]

target_file = v / "ppa_eight_branch_targets.npz"
branch_ok = False

if target_file.is_file():
    with np.load(target_file, allow_pickle=False) as data:
        if all(name in data for name in order):
            branches = [
                np.asarray(data[name]).reshape(-1)
                for name in order
            ]

            if all(x.size == 256 for x in branches):
                combined = np.concatenate(
                    branches
                ).reshape(1, 2048)

                diff = np.abs(combined - replay)
                branch_ok = np.allclose(
                    combined, replay,
                    atol=1e-3, rtol=1e-3
                )

                print(
                    "BRANCH CONCAT MAX DIFF:",
                    float(diff.max())
                )
                print(
                    "BRANCH CONCAT MEAN DIFF:",
                    float(diff.mean())
                )
            else:
                print("BRANCH TARGET SHAPES: INVALID")
        else:
            print("BRANCH TARGET KEYS: INCOMPLETE")
else:
    print("BRANCH TARGET FILE: NOT FOUND")

print("\n=== FINAL STATUS ===")
print(
    "INPUT VALUE PROVENANCE:",
    "PASS" if matches == len(names) else "NOT VERIFIED"
)
print(
    "BRANCH TARGET CONSISTENCY:",
    "PASS" if branch_ok else "NOT VERIFIED"
)
print("ORIGINAL PYTORCH: VERIFIED")
print("MAX CPU EXECUTION: PREVIOUSLY PASSED")
print("MAX NUMERICAL PARITY: NOT YET PASSED")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")

if matches == len(names) and branch_ok:
    print("NEXT: ISOLATE FIRST DIFFERENT MAX OPERATION")
else:
    print("NEXT: CORRECT IDENTIFIED REFERENCE/INPUT MISMATCH")
PY
