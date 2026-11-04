cd /application1/sajjna8/rt-pzaas-v1.0 || exit 1

M="$PWD/artifacts/v1.472-max"
V="$M/pzaas_max/validation"

test -f "$V/ppa_pytorch_reference_01.pt" || exit 1
test -f "$V/pzaas_eight_branch_targets.npz" || exit 1

podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 10g --tmpfs /tmp:rw,size=1g \
-e HOME=/tmp \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/models \
-v "$M:/models:ro" \
-v "$V:/validation:rw" \
-w /models \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import traceback
from pathlib import Path
import numpy as np
import torch

print("=== PZAAS REAL MAX SEQUENCE PARITY ===", flush=True)

try:
    from max.driver import CPU
    from max.dtype import DType
    from max.engine import InferenceSession
    from max.graph import Graph, DeviceRef, TensorType

    from pzaas_max.sequence_transformer_max import ParallelTransformerMAEPMAX
    from pzaas_max.parallel_transformer_block_2layers import ParallelTransformerBlockMAX
    from pzaas_max.sequence_postprocess_max import SequencePostprocessMAX

    ref = torch.load(
        "/validation/ppa_pytorch_reference_01.pt",
        map_location="cpu",
        weights_only=True
    )
    d = ref["model_in"]

    with np.load("/validation/pzaas_eight_branch_targets.npz") as f:
        keys = list(f.files)
        key = next(
            (k for k in keys if "sequence" in k.lower()),
            None
        )
        if key is None:
            raise KeyError(f"Sequence target absent. Keys: {keys}")
        expected = np.asarray(f[key], dtype=np.float32)

    W = Path("/models/pzaas_max/pzaas_base_weights")
    assert W.is_dir(), f"Weight directory missing: {W}"

    weights = {
        p.stem: np.ascontiguousarray(np.load(p))
        for p in W.glob("*.npy")
    }
    print("REGISTERED WEIGHTS:", len(weights), flush=True)

    def inp(name):
        return np.ascontiguousarray(
            d[name].detach().cpu().numpy().astype(np.int64)
        )

    page = inp("page_in")
    item = inp("item_in")
    meta = inp("item_meta_in")
    valid = inp("vl_in")

    wide = np.ascontiguousarray(
        d["page_meta_wide_in"][0]
        .detach().cpu().numpy()
        .astype(np.float32)
        .reshape(1, 50, 1)
    )

    inv = weights[
        "sequence_transformer.ptransformer.0.fn.rotary_emb.inv_freq"
    ].astype(np.float32)

    angles = np.arange(50, dtype=np.float32)[:, None] * inv[None, :]
    position = np.ascontiguousarray(
        np.concatenate([angles, angles], axis=-1)
        .reshape(1, 1, 50, 256)
    )

    device = DeviceRef.CPU()

    with Graph(
        "pzaas_sequence_parity",
        input_types=[
            TensorType(DType.int64, [1, 50], device=device),
            TensorType(DType.int64, [1, 50], device=device),
            TensorType(DType.int64, [1, 50], device=device),
            TensorType(DType.float32, [1, 50, 1], device=device),
            TensorType(DType.float32, [1, 1, 50, 256], device=device),
            TensorType(DType.int64, [1], device=device),
        ]
    ) as graph:
        pg, it, im, pw, pos, length = graph.inputs

        features = ParallelTransformerMAEPMAX(
            dtype=DType.float32, device=device
        )
        block0 = ParallelTransformerBlockMAX(
            dtype=DType.float32, device=device, layer_idx=0
        )
        block1 = ParallelTransformerBlockMAX(
            dtype=DType.float32, device=device, layer_idx=1
        )
        post = SequencePostprocessMAX(
            dtype=DType.float32, device=device
        )

        x = features(pg, it, im, it, pw)
        x = x + block0(x, pos, length)
        x = x + block1(x, pos, length)
        graph.output(post(x))

    print("MAX SEQUENCE GRAPH: PASS", flush=True)

    model = InferenceSession(devices=[CPU()]).load(
        graph, weights_registry=weights
    )
    print("MAX CPU COMPILATION: PASS", flush=True)

    actual = model.execute(
        page, item, meta, wide, position, valid
    )[0].to_numpy()

    print("ACTUAL SHAPE:", actual.shape)
    print("EXPECTED SHAPE:", expected.shape)

    assert actual.shape == expected.shape
    assert np.isfinite(actual).all()

    diff = np.abs(actual - expected)
    print("MAX ABS DIFF:", float(diff.max()))
    print("MEAN ABS DIFF:", float(diff.mean()))

    parity = np.allclose(
        actual, expected, rtol=1e-3, atol=1e-3
    )
    print("NUMERICAL PARITY:", "PASS" if parity else "FAIL")

    if parity:
        np.save("/validation/pzaas_sequence_max.npy", actual)
        print("PZAAS SEQUENCE PARITY: PASS")
        print("NEXT: FULL MODEL PARITY")
    else:
        print("PZAAS SEQUENCE PARITY: BLOCKED")

except Exception:
    traceback.print_exc()
    print("PZAAS SEQUENCE PARITY: BLOCKED")

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY
