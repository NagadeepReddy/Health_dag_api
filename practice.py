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
from pathlib import Path
import numpy as np
import torch
from max.graph import DeviceRef
from pzaas_max.grecbase_fusion_full_head_72_max import (
    build_grecbase_fusion_graph_order_correct
)
from pzaas_max.pzaas_weight_loader import load_weight

print("=== PZAAS EXACT 72-INPUT PACKING ===", flush=True)

root = Path("artifacts/v1.472-max/pzaas_max/validation")
p = torch.load(
    root / "ppa_model_input_exact.pt",
    map_location="cpu",
    weights_only=True
)

graph = build_grecbase_fusion_graph_order_correct(DeviceRef.CPU())
assert len(graph.inputs) == 72
print("MAX GRAPH: PASS")

def array(x):
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().numpy()
    return np.asarray(x)

def leaves(x):
    if isinstance(x, dict):
        for value in x.values():
            yield from leaves(value)
    elif isinstance(x, (list, tuple)):
        for value in x:
            yield from leaves(value)
    else:
        yield array(x)

def single(name):
    values = list(leaves(p[name]))
    assert len(values) == 1, (name, len(values))
    return values[0]

def group(name, count):
    values = list(leaves(p[name]))
    assert len(values) == count, (name, len(values))
    return values

packed = []

# 0-4: Task, IHQ and Jet
packed.extend(group("task_in", 2))
packed.append(single("ihq_in"))
packed.append(single("jet_name_in"))
packed.append(single("jet_status_in"))

# 5-22: 17 deep values and combined wide input
packed.extend(group("deep_in", 17))

wide = group("wide_in", 127)
wide = np.concatenate(
    [x.reshape(1, 1) for x in wide], axis=1
)
packed.append(wide.astype(np.float32))

# 23-24: NLP
packed.append(single("input_ids"))
packed.append(single("attention_mask"))

# 25-29: Sequence inputs
packed.append(single("page_in"))
packed.append(single("item_in"))
packed.append(single("item_meta_in"))

page_wide = single("page_meta_wide_in")
packed.append(page_wide.reshape(1, 50, 1).astype(np.float32))

# Build rotary positions from exported trained frequencies
inv = array(load_weight(
    "sequence_transformer.ptransformer.0.fn.rotary_emb.inv_freq"
)).astype(np.float32).reshape(-1)

assert inv.size == 128, f"Rotary frequency count: {inv.size}"

positions = np.arange(50, dtype=np.float32)
freq = positions[:, None] * inv[None, :]
pos = np.concatenate([freq, freq], axis=-1)
pos = pos.reshape(1, 1, 50, 256).astype(np.float32)
packed.append(pos)

# 30-69: Ten sibling groups, four tensors each
sdeep = single("sibling_deep_in")
swide = single("sibling_wide_in")

assert sdeep.shape == (1, 3, 10), sdeep.shape
assert swide.shape == (1, 18, 10), swide.shape

for i in range(10):
    for j in range(3):
        packed.append(sdeep[:, j, i])
    packed.append(swide[:, :, i])

# 70-71: Valid lengths
packed.append(single("v1_in"))
packed.append(single("sibling_v1_in"))

assert len(packed) == 72, len(packed)

print("INPUT PACKING: 72/72")
print("WIDE INPUT:", wide.shape)
print("ROTARY POSITIONS:", pos.shape)
print("SIBLING GROUPS: 10/10")

# Validate every tensor against its exact MAX type
verified = []
errors = []

for i, (value, graph_input) in enumerate(zip(packed, graph.inputs)):
    spec = str(graph_input.type)

    dtype_match = re.search(r"dtype=(int64|float32)", spec)
    shape_match = re.search(r"shape=\[([^\]]+)\]", spec)

    if not dtype_match or not shape_match:
        errors.append((i, "Unrecognized MAX type", spec))
        continue

    expected_dtype = np.dtype(dtype_match.group(1))
    expected_shape = tuple(
        int(n) for n in re.findall(
            r"Dim\((\d+)\)", shape_match.group(1)
        )
    )

    actual = np.asarray(value)

    if actual.shape != expected_shape:
        errors.append((
            i, "SHAPE", actual.shape, expected_shape
        ))
        continue

    if not np.can_cast(actual.dtype, expected_dtype, casting="safe"):
        errors.append((
            i, "DTYPE", str(actual.dtype), str(expected_dtype)
        ))
        continue

    verified.append(actual.astype(expected_dtype, copy=False))

if errors:
    print("INPUT VALIDATION: BLOCKED")
    for error in errors:
        print("MISMATCH:", error)
    raise SystemExit(1)

assert len(verified) == 72
print("SHAPE AND DTYPE VALIDATION: 72/72 PASS")

# Save only into isolated PZAAS MAX validation directory.
out = root / "ppa_packed_inputs_72_verified.npz"
data = {
    f"input_{i:02d}": value
    for i, value in enumerate(verified)
}

if out.exists():
    with np.load(out, allow_pickle=False) as old:
        same = (
            set(old.files) == set(data)
            and all(
                np.array_equal(old[k], v, equal_nan=True)
                if np.issubdtype(v.dtype, np.inexact)
                else np.array_equal(old[k], v)
                for k, v in data.items()
            )
        )
    if not same:
        raise RuntimeError(
            "Existing packed file differs; refusing to overwrite"
        )
    print("EXISTING PACKED FILE: VERIFIED")
else:
    np.savez_compressed(out, **data)
    print("PACKED INPUT FILE: SAVED")

with np.load(out, allow_pickle=False) as saved:
    assert len(saved.files) == 72
    for i, value in enumerate(verified):
        key = f"input_{i:02d}"
        assert np.array_equal(saved[key], value, equal_nan=True) \
            if np.issubdtype(value.dtype, np.inexact) \
            else np.array_equal(saved[key], value)

print("=== RESULTS ===")
print("MAX GRAPH: PASS")
print("EXACT INPUT COUNT: 72/72 PASS")
print("INPUT SHAPES: PASS")
print("INPUT DTYPES: PASS")
print("PACKED DATA VALIDATION: PASS")
print("OUTPUT FILE:", out)
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: EXECUTE MAX AND CHECK FULL NUMERICAL PARITY")
PY
