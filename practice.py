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
import torch
from pathlib import Path
from max.graph import DeviceRef
from pzaas_max.grecbase_fusion_full_head_72_max import (
    build_grecbase_fusion_graph_order_correct
)
from pzaas_max.pzaas_weight_loader import load_weight

root = Path("artifacts/v1.472-max/pzaas_max/validation")

print("=== PZAAS CORRECTED EXACT 72-INPUT PACKING ===", flush=True)

p = torch.load(
    root / "ppa_model_input_exact.pt",
    map_location="cpu",
    weights_only=True
)

with np.load(root / "ppa_tensor_inputs.npz", allow_pickle=False) as z:
    auxiliary = {k: z[k].copy() for k in z.files}

def arr(x):
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().numpy()
    return np.asarray(x)

def flatten(x):
    if isinstance(x, dict):
        for value in x.values():
            yield from flatten(value)
    elif isinstance(x, (list, tuple)):
        for value in x:
            yield from flatten(value)
    else:
        yield arr(x)

def get(name, count=1):
    if name in p:
        values = list(flatten(p[name]))
    elif name in auxiliary:
        values = [auxiliary[name]]
        print("RECOVERED FROM NPZ:", name)
    else:
        raise RuntimeError(f"Missing saved input: {name}")

    if len(values) != count:
        raise RuntimeError(
            f"{name}: expected {count}, found {len(values)}"
        )
    return values

graph = build_grecbase_fusion_graph_order_correct(DeviceRef.CPU())
assert len(graph.inputs) == 72
print("MAX GRAPH: PASS")

packed = []

# Task and jet inputs: 0-4
packed += get("task_in", 2)
packed += get("ihq_in")
packed += get("jet_name_in")
packed += get("jet_status_in")

# Context inputs: 5-22
packed += get("deep_in", 17)

wide = np.concatenate([
    x.reshape(1, 1) for x in get("wide_in", 127)
], axis=1).astype(np.float32)

packed.append(wide)

# NLP: 23-24
packed += get("input_ids")
packed += get("attention_mask")

# Sequence: 25-29
packed += get("page_in")
packed += get("item_in")
packed += get("item_meta_in")

page_wide = get("page_meta_wide_in")[0]
packed.append(
    page_wide.reshape(1, 50, 1).astype(np.float32)
)

inv = arr(load_weight(
    "sequence_transformer.ptransformer.0.fn.rotary_emb.inv_freq"
)).astype(np.float32).reshape(-1)

assert inv.size == 128

freq = np.arange(50, dtype=np.float32)[:, None] * inv[None, :]
pos = np.concatenate([freq, freq], axis=-1)
packed.append(pos.reshape(1, 1, 50, 256))

# Siblings: 30-69
sdeep = get("sibling_deep_in")[0]
swide = get("sibling_wide_in")[0]

assert sdeep.shape == (1, 3, 10)
assert swide.shape == (1, 18, 10)

for i in range(10):
    for j in range(3):
        packed.append(sdeep[:, j, i])
    packed.append(swide[:, :, i])

# Final length inputs: 70-71
# Corrected lookup automatically uses saved NPZ.
packed += get("v1_in")
packed += get("sibling_v1_in")

assert len(packed) == 72
print("PACKED INPUT COUNT: 72/72 PASS")

verified = []
errors = []

for i, (value, tensor) in enumerate(zip(packed, graph.inputs)):
    spec = str(tensor.type)
    dm = re.search(r"dtype=(int64|float32)", spec)
    sm = re.search(r"shape=\[([^\]]+)\]", spec)

    if not dm or not sm:
        errors.append((i, "Unknown graph signature", spec))
        continue

    dtype = np.dtype(dm.group(1))
    shape = tuple(
        int(x) for x in re.findall(
            r"Dim\((\d+)\)", sm.group(1)
        )
    )

    value = np.asarray(value)

    if value.shape != shape:
        errors.append((i, "shape", value.shape, shape))
        continue

    if not np.can_cast(value.dtype, dtype, casting="safe"):
        errors.append((i, "dtype", str(value.dtype), str(dtype)))
        continue

    verified.append(value.astype(dtype, copy=False))

if errors:
    print("VALIDATION: BLOCKED")
    for error in errors:
        print("MISMATCH:", error)
    raise SystemExit(1)

print("ALL 72 SHAPES: PASS")
print("ALL 72 DTYPES: PASS")

output = root / "ppa_packed_inputs_72_verified.npz"

data = {
    f"input_{i:02d}": v
    for i, v in enumerate(verified)
}

if output.exists():
    with np.load(output, allow_pickle=False) as z:
        same = (
            set(z.files) == set(data)
            and all(
                np.array_equal(z[k], v, equal_nan=True)
                for k, v in data.items()
            )
        )
    if not same:
        raise RuntimeError(
            "Existing packed inputs differ; not overwriting"
        )
    print("EXISTING PACKED INPUTS: VERIFIED")
else:
    np.savez_compressed(output, **data)
    print("PACKED INPUTS: SAVED")

print("\n=== FINAL RESULTS ===")
print("MAX GRAPH: PASS")
print("EXACT 72 INPUTS: PASS")
print("SHAPE / DTYPE: PASS")
print("OUTPUT:", output)
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: REAL MAX NUMERICAL PARITY")
PY
