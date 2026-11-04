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

print("=== PZAAS EXACT 72-INPUT FIX ===", flush=True)

root = Path("artifacts/v1.472-max/pzaas_max/validation")

p = torch.load(
    root / "ppa_model_input_exact.pt",
    map_location="cpu",
    weights_only=True
)

with np.load(root / "ppa_tensor_inputs.npz", allow_pickle=False) as z:
    auxiliary = {k: z[k].copy() for k in z.files}

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

def get(name, count=1):
    if name in p:
        values = list(leaves(p[name]))
    elif name in auxiliary:
        values = [auxiliary[name]]
    else:
        raise RuntimeError(
            f"Missing input {name}; available NPZ keys: "
            f"{sorted(auxiliary)}"
        )

    if len(values) != count:
        raise RuntimeError(
            f"{name}: expected {count}, found {len(values)}"
        )

    return values

graph = build_grecbase_fusion_graph_order_correct(
    DeviceRef.CPU()
)

assert len(graph.inputs) == 72
print("MAX GRAPH: PASS")

packed = []

packed += get("task_in", 2)
packed += get("ihq_in")
packed += get("jet_name_in")
packed += get("jet_status_in")

packed += get("deep_in", 17)

wide = np.concatenate(
    [x.reshape(1, 1) for x in get("wide_in", 127)],
    axis=1
).astype(np.float32)

packed.append(wide)

packed += get("input_ids")
packed += get("attention_mask")

packed += get("page_in")
packed += get("item_in")
packed += get("item_meta_in")

page_wide = get("page_meta_wide_in")[0]
packed.append(
    page_wide.reshape(1, 50, 1).astype(np.float32)
)

inv = array(load_weight(
    "sequence_transformer.ptransformer.0.fn.rotary_emb.inv_freq"
)).astype(np.float32).reshape(-1)

assert inv.size == 128

freq = np.arange(50, dtype=np.float32)[:, None] * inv[None, :]
pos = np.concatenate([freq, freq], axis=-1)
packed.append(pos.reshape(1, 1, 50, 256))

sdeep = get("sibling_deep_in")[0]
swide = get("sibling_wide_in")[0]

assert sdeep.shape == (1, 3, 10)
assert swide.shape == (1, 18, 10)

for i in range(10):
    for j in range(3):
        packed.append(sdeep[:, j, i])
    packed.append(swide[:, :, i])

# Correct spelling: lowercase L, not digit 1.
packed += get("vl_in")
packed += get("sibling_vl_in")

assert len(packed) == 72
print("EXACT INPUT COUNT: 72/72 PASS")
print("VALID LENGTH INPUTS: FOUND")

verified = []
errors = []

for i, (value, tensor) in enumerate(zip(packed, graph.inputs)):
    spec = str(tensor.type)

    dm = re.search(r"dtype=(int64|float32)", spec)
    sm = re.search(r"shape=\[([^\]]+)\]", spec)

    if dm is None or sm is None:
        errors.append((i, "Unsupported graph signature", spec))
        continue

    expected_dtype = np.dtype(dm.group(1))
    expected_shape = tuple(
        int(x) for x in re.findall(
            r"Dim\((\d+)\)", sm.group(1)
        )
    )

    value = np.asarray(value)

    if value.shape != expected_shape:
        errors.append(
            (i, "SHAPE", value.shape, expected_shape)
        )
        continue

    if not np.can_cast(
        value.dtype, expected_dtype, casting="safe"
    ):
        errors.append(
            (i, "DTYPE", str(value.dtype), str(expected_dtype))
        )
        continue

    verified.append(
        value.astype(expected_dtype, copy=False)
    )

if errors:
    print("VALIDATION: BLOCKED")
    for error in errors:
        print("MISMATCH:", error)
    raise SystemExit(1)

assert len(verified) == 72

print("ALL 72 INPUT SHAPES: PASS")
print("ALL 72 INPUT DTYPES: PASS")

output = root / "ppa_packed_inputs_72_verified.npz"

data = {
    f"input_{i:02d}": value
    for i, value in enumerate(verified)
}

if output.exists():
    with np.load(output, allow_pickle=False) as old:
        identical = (
            set(old.files) == set(data)
            and all(
                old[k].dtype == value.dtype
                and old[k].shape == value.shape
                and np.array_equal(old[k], value)
                for k, value in data.items()
            )
        )
    if not identical:
        raise RuntimeError(
            "Existing packed file differs; refusing overwrite"
        )
    print("PACKED INPUTS: EXISTING FILE VERIFIED")
else:
    np.savez_compressed(output, **data)
    print("PACKED INPUTS: SAVED")

print("=== PZAAS RESULTS ===")
print("GRAPH: PASS")
print("72 INPUTS: PASS")
print("SHAPES AND DTYPES: PASS")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: REAL MAX EXECUTION AND NUMERICAL PARITY")
PY
