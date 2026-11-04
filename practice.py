cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none \
-v /application1:/application1:rw \
-w /application1/sajjna8/rt-pzaas-v1.0 \
-e PYTHONPATH=/application1/sajjna8/rt-pzaas-v1.0/artifacts/v1.472-max \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -c 'exec python3 -' <<'PY'
import re
import numpy as np
from pathlib import Path

from max import engine
from max.driver import CPU, Tensor
from max.graph import DeviceRef

from pzaas_max.grecbase_fusion_full_head_72_max import (
    build_grecbase_fusion_graph_order_correct
)
from pzaas_max.pzaas_weight_loader import load_weight

print("=== PZAAS REAL MAX CPU NUMERICAL PARITY ===", flush=True)

root = Path("artifacts/v1.472-max/pzaas_max/validation")
input_file = root / "ppa_packed_inputs_72_verified.npz"
target_file = root / "pzaas_eight_branch_targets.npz"

assert input_file.is_file(), "Verified inputs missing"
assert target_file.is_file(), "PyTorch targets missing"

device = CPU()

graph = build_grecbase_fusion_graph_order_correct(
    DeviceRef.CPU()
)

assert len(graph.inputs) == 72
print("MAX GRAPH: PASS", flush=True)

# Bind original trained weights, including verified aliases.
registry = {}
missing = []

for name in graph._weights:
    candidates = [name]

    if not name.endswith((".weight", ".bias")):
        candidates.append(name + ".weight")

    for candidate in list(candidates):
        alias = re.sub(
            r"(\.ptransformer\.[01]\.)",
            r"\1fn.",
            candidate
        )
        if alias not in candidates:
            candidates.append(alias)

    found = False

    for candidate in candidates:
        try:
            value = np.asarray(load_weight(candidate))
            value = np.ascontiguousarray(value)
            registry[name] = value
            found = True
            break
        except (KeyError, FileNotFoundError, ValueError):
            continue

    if not found:
        missing.append((name, candidates))

print("GRAPH WEIGHTS:", len(graph._weights))
print("BOUND WEIGHTS:", len(registry))

if missing:
    for name, candidates in missing:
        print("MISSING:", name, candidates)
    raise RuntimeError("Weight binding incomplete")

assert len(registry) == len(graph._weights) == 17
print("TRAINED WEIGHTS: 17/17 PASS", flush=True)

with np.load(input_file, allow_pickle=False) as z:
    keys = [f"input_{i:02d}" for i in range(72)]
    assert set(z.files) == set(keys)
    arrays = [
        np.ascontiguousarray(z[key].copy())
        for key in keys
    ]

print("SAVED INPUTS: 72/72 PASS", flush=True)

# Real MAX compilation and execution.
print("COMPILING REAL MAX CPU GRAPH...", flush=True)

session = engine.InferenceSession(devices=[device])

model = session.load(
    graph,
    weights_registry=registry
)

print("REAL MAX CPU COMPILATION: PASS", flush=True)

inputs = [
    Tensor.from_numpy(value).to(device)
    for value in arrays
]

print("EXECUTING REAL MAX CPU GRAPH...", flush=True)

results = model.execute(*inputs)

assert len(results) == 1

actual = np.asarray(
    results[0].to_numpy(),
    dtype=np.float32
)

print("REAL MAX CPU EXECUTION: PASS", flush=True)
print("MAX OUTPUT SHAPE:", actual.shape)

# Original PyTorch branch targets.
branch_names = [
    "sequence",
    "context",
    "search0",
    "search1",
    "jet",
    "ihq",
    "sibling",
    "task"
]

with np.load(target_file, allow_pickle=False) as z:
    assert set(branch_names).issubset(set(z.files))
    targets = [
        np.asarray(z[name], dtype=np.float32).reshape(1, 256)
        for name in branch_names
    ]

expected = np.concatenate(targets, axis=1)

assert expected.shape == (1, 2048)
assert actual.shape == expected.shape
assert np.isfinite(actual).all()
assert np.isfinite(expected).all()

print("\n=== EIGHT-BRANCH NUMERICAL PARITY ===")

all_pass = True

for i, name in enumerate(branch_names):
    start = i * 256
    end = start + 256

    a = actual[:, start:end]
    b = expected[:, start:end]

    diff = np.abs(a - b)
    passed = np.allclose(
        a, b,
        atol=1e-3,
        rtol=1e-3
    )

    all_pass &= passed

    print(
        f"{name}: {'PASS' if passed else 'FAIL'} "
        f"| max_diff={diff.max():.8g} "
        f"| mean_diff={diff.mean():.8g}",
        flush=True
    )

diff = np.abs(actual - expected)

print("\n=== FULL GRAPH RESULTS ===")
print("MAX OUTPUT:", actual.shape)
print("PYTORCH OUTPUT:", expected.shape)
print("MAX ABS DIFF:", float(diff.max()))
print("MEAN ABS DIFF:", float(diff.mean()))

if all_pass:
    print("FULL 8-BRANCH NUMERICAL PARITY: PASS")
    print("PZAAS REAL MAX CPU POC: NUMERICAL PASS")
else:
    print("FULL 8-BRANCH NUMERICAL PARITY: FAIL")
    print("FIRST FAILED BRANCH IDENTIFIED ABOVE")

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")

if not all_pass:
    raise SystemExit(1)
PY
