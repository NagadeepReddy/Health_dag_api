cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network=none \
-v "$PWD:/workspace:ro" -w /workspace \
--entrypoint python localhost/cta-max-faiss:local - <<'PY'
from pathlib import Path
from collections.abc import Mapping
import torch
import numpy as np
import re
import traceback

print("=== PZAAS DIRECT CHECKPOINT / MAX WEIGHT PARITY ===", flush=True)

root = Path("/workspace")
checkpoint = root / "artifacts/v1.472/core-artifact/model_0_base.pt"
max_root = root / "artifacts/v1.472-max/pzaas_max"

try:
    assert checkpoint.is_file(), f"Missing checkpoint: {checkpoint}"
    assert max_root.is_dir(), f"Missing MAX directory: {max_root}"

    try:
        obj = torch.load(checkpoint, map_location="cpu", weights_only=True)
    except Exception:
        obj = torch.load(checkpoint, map_location="cpu", weights_only=False)

    candidates = []

    def collect(value, label="root", depth=0):
        if isinstance(value, torch.nn.Module):
            collect(value.state_dict(), label + ".state_dict", depth + 1)
        elif isinstance(value, Mapping):
            tensors = {
                str(k): v for k, v in value.items()
                if isinstance(v, torch.Tensor)
            }
            if tensors:
                candidates.append((label, tensors))
            if depth < 4:
                for k, v in value.items():
                    if isinstance(v, Mapping) or isinstance(v, torch.nn.Module):
                        collect(v, label + "." + str(k), depth + 1)

    collect(obj)
    assert candidates, "No tensor state dictionary found"

    label, state = max(candidates, key=lambda x: len(x[1]))
    print("CHECKPOINT LOAD: PASS")
    print("STATE SOURCE:", label)
    print("TRAINED TENSORS:", len(state))

    pattern = re.compile(r"(?:^|\.)ptransformer\.(\d+)\.")
    layers = sorted({
        int(m.group(1))
        for key in state
        if (m := pattern.search(key))
    })

    print("TRAINED TRANSFORMER LAYERS:", layers)

    for layer in layers:
        count = sum(
            f"ptransformer.{layer}." in k
            for k in state
        )
        print(f"LAYER {layer} TRAINED TENSORS: {count}")

    files = list(max_root.rglob("*.npy"))
    print("EXPORTED NPY FILES FOUND:", len(files))

    by_name = {}
    for p in files:
        by_name.setdefault(p.stem, []).append(p)

    matched = 0
    mismatched = []
    unresolved = []

    for key, tensor in state.items():
        names = [
            key,
            key.removeprefix("module."),
            key.removeprefix("model."),
            key.removeprefix("model_base."),
        ]

        paths = []
        for name in names:
            paths.extend(by_name.get(name, []))

        paths = list(dict.fromkeys(paths))

        if len(paths) != 1:
            unresolved.append(key)
            continue

        try:
            actual = np.load(paths[0], allow_pickle=False)
            expected = tensor.detach().cpu().numpy()

            if actual.shape != expected.shape:
                mismatched.append((key, "shape mismatch"))
                continue

            if not np.allclose(
                actual, expected,
                rtol=1e-6, atol=1e-6,
                equal_nan=True
            ):
                diff = np.max(np.abs(
                    actual.astype(np.float64) -
                    expected.astype(np.float64)
                ))
                mismatched.append((key, f"max diff {diff}"))
                continue

            matched += 1

        except Exception as exc:
            mismatched.append((key, str(exc)))

    print("EXACT WEIGHT MATCHES:", matched)
    print("WEIGHT MISMATCHES:", len(mismatched))
    print("UNRESOLVED WEIGHT NAMES:", len(unresolved))

    for item in mismatched[:10]:
        print("MISMATCH:", item)

    for item in unresolved[:10]:
        print("UNRESOLVED:", item)

    if mismatched:
        print("WEIGHT PARITY: FAIL")
    elif unresolved:
        print("WEIGHT PARITY: PARTIAL - MAPPING INCOMPLETE")
    else:
        print("WEIGHT PARITY: PASS")

    print("EFFECTIVE TRAINED DEPTH:", len(layers))
    print("FULL MODEL NUMERICAL PARITY: NOT YET VERIFIED")

except Exception:
    traceback.print_exc(limit=6)
    print("CHECKPOINT VALIDATION: BLOCKED")

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: RESOLVE EXACT MAX SEQUENCE DIVERGENCE")
PY
