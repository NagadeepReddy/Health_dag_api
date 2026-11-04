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
import ast
import importlib
import traceback
from pathlib import Path
import numpy as np
import torch
from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import Graph, DeviceRef, TensorType, ops
from pzaas_max import grecbase_fusion_full_head_72_max as m

print("=== PZAAS CONTEXT + SEQUENCE PARITY RETRY ===", flush=True)

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
results = {}

def resolve_class(name):
    existing = getattr(m, name, None)
    if existing is not None:
        return existing

    for p in Path("/models/pzaas_max").glob("*.py"):
        tree = ast.parse(p.read_text())
        if any(
            isinstance(n, ast.ClassDef) and n.name == name
            for n in tree.body
        ):
            module = importlib.import_module(
                "pzaas_max." + p.stem
            )
            return getattr(module, name)

    raise ImportError("MAX class not found: " + name)

def verify(name, actual):
    expected = targets[name]
    actual = np.asarray(actual)

    print(name.upper(), "SHAPE:", actual.shape, flush=True)

    if actual.shape != expected.shape:
        print(name.upper(), "EXPECTED:", expected.shape)
        return False

    if not np.isfinite(actual).all():
        print(name.upper(), "NON-FINITE OUTPUT")
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

# CONTEXT
print("\n=== CONTEXT REAL MAX ===", flush=True)

try:
    deep = [
        np.ascontiguousarray(
            x.detach().cpu().numpy().astype(np.int64)
        )
        for x in d["deep_in"]
    ]

    wide = np.ascontiguousarray(
        np.concatenate([
            x.detach().cpu().numpy().reshape(1, -1)
            for x in d["wide_in"]
        ], axis=1).astype(np.float32)
    )

    assert len(deep) == 17
    assert wide.shape == (1, 127)

    with Graph(
        "pzaas_context_fixed",
        input_types=[
            TensorType(DType.int64, [1], device=device)
            for _ in range(17)
        ] + [
            TensorType(DType.float32, [1, 127], device=device)
        ]
    ) as graph:
        result = m.main_context_forward(
            graph.inputs[:17],
            graph.inputs[17],
            device
        )

        # Context also returns an auxiliary embedding
        context = result[0] if isinstance(
            result, (tuple, list)
        ) else result

        graph.output(context)

    print("CONTEXT GRAPH: PASS", flush=True)

    model = InferenceSession(
        devices=[CPU()]
    ).load(graph, weights_registry=weights)

    print("CONTEXT CPU COMPILATION: PASS", flush=True)

    actual = model.execute(*deep, wide)[0].to_numpy()
    results["context"] = verify("context", actual)

except Exception:
    traceback.print_exc()
    results["context"] = False
    print("CONTEXT: BLOCKED")

# SEQUENCE
print("\n=== SEQUENCE REAL MAX ===", flush=True)

try:
    Features = resolve_class("ParallelTransformerFfMAPMAX")
    Block = resolve_class("ParallelTransformerBlockMAX")
    Postprocess = resolve_class("SequencePostprocessMAX")

    print("SEQUENCE CLASS IMPORTS: PASS", flush=True)

    def arr(key):
        return np.ascontiguousarray(
            d[key].detach().cpu().numpy().astype(np.int64)
        )

    page = arr("page_in")
    item = arr("item_in")
    meta = arr("item_meta_in")
    wide = np.ascontiguousarray(
        d["page_meta_wide_in"][0]
        .detach().cpu().numpy().astype(np.int64)
    )
    valid = arr("vl_in")

    inv = weights["att_pooling.rotary_emb.inv_freq"].astype(
        np.float32
    )

    angles = (
        np.arange(50, dtype=np.float32)[:, None]
        * inv[None, :]
    )

    position = np.ascontiguousarray(
        np.concatenate(
            [angles, angles], axis=-1
        ).reshape(1, 1, 50, 256)
    )

    with Graph(
        "pzaas_sequence_fixed",
        input_types=[
            TensorType(DType.int64, [1, 50], device=device)
            for _ in range(4)
        ] + [
            TensorType(
                DType.float32,
                [1, 1, 50, 256],
                device=device
            ),
            TensorType(DType.int64, [1], device=device)
        ]
    ) as graph:
        pg, it, im, pw, pos, length = graph.inputs

        features = Features(dtype=DType.float32, device=device)
        block0 = Block(
            dtype=DType.float32, device=device, layer_idx=0
        )
        block1 = Block(
            dtype=DType.float32, device=device, layer_idx=1
        )
        post = Postprocess(dtype=DType.float32, device=device)

        sx = features(pg, it, im, it, pw)
        sx1 = sx + block0(sx, pos, length)
        sx2 = sx1 + block1(sx1, pos, length)
        raw = post(sx2)

        if isinstance(raw, (tuple, list)):
            raw = raw[0]

        sw = weights["seq_dense.weight"].astype(np.float32)
        sb = weights["seq_dense.bias"].astype(np.float32)

        output = ops.matmul(
            raw,
            ops.constant(
                sw.T, dtype=DType.float32, device=device
            )
        ) + ops.constant(
            sb, dtype=DType.float32, device=device
        )

        graph.output(output)

    print("SEQUENCE GRAPH: PASS", flush=True)

    model = InferenceSession(
        devices=[CPU()]
    ).load(graph, weights_registry=weights)

    print("SEQUENCE CPU COMPILATION: PASS", flush=True)

    actual = model.execute(
        page, item, meta, wide, position, valid
    )[0].to_numpy()

    results["sequence"] = verify("sequence", actual)

except Exception:
    traceback.print_exc()
    results["sequence"] = False
    print("SEQUENCE: BLOCKED")

print("\n=== FINAL RESULTS ===")
for name in ("context", "sequence"):
    print(
        name.upper() + " PARITY:",
        "PASS" if results[name] else "BLOCKED"
    )

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")

if all(results.values()):
    print("PZAAS EIGHT BRANCH PARITY: PASS")
    print("NEXT: FULL MAX MODEL PARITY")
else:
    print("NEXT: RESOLVE REMAINING NUMERICAL ISSUE")
PY
