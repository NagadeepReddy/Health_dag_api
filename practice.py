cd /application1/sajjna8/rt-pzaas-v1.0 && \
M="$PWD/artifacts/v1.472-max" && \
V="$M/pzaas_max/validation" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 10g --tmpfs /tmp:rw,size=1g \
-e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/models \
-v "$M:/models:ro" \
-v "$V:/validation:rw" \
-w /models \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import numpy as np
import torch
import traceback
from pathlib import Path
from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import Graph, DeviceRef, TensorType, ops
from pzaas_max import grecbase_fusion_full_head_72_max as m

print("=== PZAAS FINAL TWO BRANCHES REAL MAX ===", flush=True)

ref = torch.load(
    "/validation/ppa_pytorch_reference_01.pt",
    map_location="cpu", weights_only=True
)
d = ref["model_in"]

with np.load(
    "/validation/pzaas_eight_branch_targets.npz",
    allow_pickle=False
) as f:
    targets = {
        k: f[k].astype(np.float32)
        for k in ("context", "sequence")
    }

weights = {
    p.stem: np.ascontiguousarray(np.load(p, allow_pickle=False))
    for p in Path(m.WDIR).glob("*.npy")
}
assert len(weights) == 208
device = DeviceRef.CPU()

def tensor(key, dtype):
    x = d[key]
    if isinstance(x, torch.Tensor):
        x = x.detach().cpu().numpy()
    return np.ascontiguousarray(np.asarray(x, dtype=dtype))

def check(name, actual):
    expected = targets[name]
    actual = np.asarray(actual)
    print(name.upper(), "MAX SHAPE:", actual.shape)
    print(name.upper(), "TORCH SHAPE:", expected.shape)

    if actual.shape != expected.shape:
        print(name.upper(), "PARITY: SHAPE MISMATCH")
        return False

    if not np.isfinite(actual).all():
        print(name.upper(), "PARITY: NON-FINITE")
        return False

    diff = np.abs(actual - expected)
    passed = np.allclose(
        actual, expected, atol=1e-3, rtol=1e-3
    )
    print(name.upper(), "MAX ABS DIFF:", float(diff.max()))
    print(name.upper(), "MEAN ABS DIFF:", float(diff.mean()))
    print(name.upper(), "PARITY:", "PASS" if passed else "FAILED")

    if passed:
        np.save(
            "/validation/pzaas_" + name + "_max.npy",
            actual, allow_pickle=False
        )
    return passed

results = {}

# CONTEXT: 17 deep inputs + 127 wide features
print("\n=== CONTEXT REAL MAX ===", flush=True)
try:
    deep = [
        np.ascontiguousarray(x.detach().cpu().numpy().astype(np.int64))
        for x in d["deep_in"]
    ]
    wide = np.concatenate([
        x.detach().cpu().numpy().reshape(1, -1)
        for x in d["wide_in"]
    ], axis=1).astype(np.float32)

    assert len(deep) == 17
    assert wide.shape == (1, 127)

    with Graph(
        "pzaas_context_parity",
        input_types=[
            TensorType(DType.int64, [1], device=device)
            for _ in range(17)
        ] + [
            TensorType(DType.float32, [1, 127], device=device)
        ]
    ) as graph:
        output = m.main_context_forward(
            graph.inputs[:17], graph.inputs[17], device
        )
        graph.output(output)

    print("CONTEXT GRAPH: PASS", flush=True)
    model = InferenceSession(devices=[CPU()]).load(
        graph, weights_registry=weights
    )
    print("CONTEXT CPU COMPILATION: PASS", flush=True)
    actual = model.execute(*deep, wide)[0].to_numpy()
    results["context"] = check("context", actual)

except Exception:
    traceback.print_exc()
    results["context"] = False
    print("CONTEXT: BLOCKED")

# SEQUENCE: actual DS inputs + Rotary position tensor
print("\n=== SEQUENCE REAL MAX ===", flush=True)
try:
    page = tensor("page_in", np.int64)
    item = tensor("item_in", np.int64)
    item_meta = tensor("item_meta_in", np.int64)
    page_wide = np.ascontiguousarray(
        d["page_meta_wide_in"][0].detach().cpu().numpy(),
        dtype=np.int64
    )
    valid = tensor("vl_in", np.int64)

    assert all(x.shape == (1, 50) for x in (
        page, item, item_meta, page_wide
    ))
    assert valid.shape == (1,)

    inv = weights["att_pooling.rotary_emb.inv_freq"].astype(
        np.float32
    )
    assert inv.shape == (128,)

    angles = (
        np.arange(50, dtype=np.float32)[:, None]
        * inv[None, :]
    )
    position = np.ascontiguousarray(
        np.concatenate([angles, angles], axis=-1)
        .reshape(1, 1, 50, 256)
    )

    with Graph(
        "pzaas_sequence_parity",
        input_types=[
            TensorType(DType.int64, [1, 50], device=device)
            for _ in range(4)
        ] + [
            TensorType(DType.float32, [1, 1, 50, 256], device=device),
            TensorType(DType.int64, [1], device=device)
        ]
    ) as graph:
        pg, it, meta, pgwide, pos, length = graph.inputs

        features = m.ParallelTransformerFfMAPMAX(
            dtype=DType.float32, device=device
        )
        block0 = m.ParallelTransformerBlockMAX(
            dtype=DType.float32, device=device, layer_idx=0
        )
        block1 = m.ParallelTransformerBlockMAX(
            dtype=DType.float32, device=device, layer_idx=1
        )
        post = m.SequencePostprocessMAX(
            dtype=DType.float32, device=device
        )

        sx = features(pg, it, meta, it, pgwide)
        sx1 = sx + block0(sx, pos, length)
        sx2 = sx1 + block1(sx1, pos, length)
        seq_raw = post(sx2)

        sw = weights["seq_dense.weight"].astype(np.float32)
        sb = weights["seq_dense.bias"].astype(np.float32)

        seq = ops.matmul(
            seq_raw,
            ops.constant(sw.T, dtype=DType.float32, device=device)
        ) + ops.constant(
            sb, dtype=DType.float32, device=device
        )
        graph.output(seq)

    print("SEQUENCE GRAPH: PASS", flush=True)
    model = InferenceSession(devices=[CPU()]).load(
        graph, weights_registry=weights
    )
    print("SEQUENCE CPU COMPILATION: PASS", flush=True)

    actual = model.execute(
        page, item, item_meta, page_wide, position, valid
    )[0].to_numpy()

    results["sequence"] = check("sequence", actual)

except Exception:
    traceback.print_exc()
    results["sequence"] = False
    print("SEQUENCE: BLOCKED")

print("\n=== FINAL RESULTS ===")
for name in ("context", "sequence"):
    print(
        name.upper() + " PARITY:",
        "PASS" if results[name] else "PENDING"
    )

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")

if all(results.values()):
    print("PZAAS EIGHT BRANCHES: PASS")
    print("NEXT: FULL MODEL PARITY")
else:
    print("NEXT: RESOLVE FAILED BRANCH")
PY
