cd /application1/sajjna8/rt-pzaas-v1.0 && \
M="$PWD/artifacts/v1.472-max" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 10g --tmpfs /tmp:rw,size=1g \
-e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/models \
-v "$M:/models:ro" \
-v "$M/validation:/validation:rw" \
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

    from pzaas_max import grecbase_fusion_full_head_72_max as m
    from pzaas_max.sequence_transformer_max import (
        ParallelTransformerMAEPMAX
    )
    from pzaas_max.parallel_transformer_block_2layers import (
        ParallelTransformerBlockMAX
    )
    from pzaas_max.sequence_postprocess_max import (
        SequencePostprocessMAX
    )

    print("MAX SEQUENCE IMPORTS: PASS", flush=True)

    ref = torch.load(
        "/validation/ppa_pytorch_reference_01.pt",
        map_location="cpu",
        weights_only=True
    )
    d = ref["model_in"]

    with np.load(
        "/validation/pzaas_eight_branch_targets.npz",
        allow_pickle=False
    ) as f:
        expected = f["sequence"].astype(np.float32)

    weights = {
        p.stem: np.ascontiguousarray(
            np.load(p, allow_pickle=False)
        )
        for p in Path(m.WDIR).glob("*.npy")
    }

    assert len(weights) == 208

    def tensor(name, dtype=np.int64):
        return np.ascontiguousarray(
            d[name].detach().cpu().numpy().astype(dtype)
        )

    page = tensor("page_in")
    item = tensor("item_in")
    meta = tensor("item_meta_in")
    valid = tensor("vl_in")

    wide = np.ascontiguousarray(
        d["page_meta_wide_in"][0]
        .detach().cpu().numpy()
        .astype(np.float32)
        .reshape(1, 50, 1)
    )

    inv = weights[
        "sequence_transformer.ptransformer.0.fn.rotary_emb.inv_freq"
    ].astype(np.float32)

    angles = (
        np.arange(50, dtype=np.float32)[:, None]
        * inv[None, :]
    )

    position = np.ascontiguousarray(
        np.concatenate(
            [angles, angles], axis=-1
        ).reshape(1, 1, 50, 256)
    )

    device = DeviceRef.CPU()

    with Graph(
        "pzaas_sequence_real_parity",
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
            dtype=DType.float32,
            device=device
        )

        block0 = ParallelTransformerBlockMAX(
            dtype=DType.float32,
            device=device,
            layer_idx=0
        )

        block1 = ParallelTransformerBlockMAX(
            dtype=DType.float32,
            device=device,
            layer_idx=1
        )

        postprocess = SequencePostprocessMAX(
            dtype=DType.float32,
            device=device
        )

        sx = features(pg, it, im, it, pw)
        sx1 = sx + block0(sx, pos, length)
        sx2 = sx1 + block1(sx1, pos, length)

        # Already contains pooling and seq_dense.
        output = postprocess(sx2)

        graph.output(output)

    print("MAX SEQUENCE GRAPH: PASS", flush=True)

    model = InferenceSession(
        devices=[CPU()]
    ).load(graph, weights_registry=weights)

    print("REAL MAX CPU COMPILATION: PASS", flush=True)

    actual = model.execute(
        page, item, meta, wide, position, valid
    )[0].to_numpy()

    print("ACTUAL SHAPE:", actual.shape)
    print("EXPECTED SHAPE:", expected.shape)

    assert actual.shape == expected.shape
    assert np.isfinite(actual).all()

    diff = np.abs(actual - expected)
    mean_diff = float(diff.mean())
    max_diff = float(diff.max())

    print("MAX ABS DIFF:", max_diff)
    print("MEAN ABS DIFF:", mean_diff)

    assert np.allclose(
        actual, expected,
        atol=1e-3,
        rtol=1e-3
    ), "Sequence numerical parity mismatch"

    np.save(
        "/validation/pzaas_sequence_max.npy",
        actual,
        allow_pickle=False
    )

    print("PZAAS SEQUENCE PARITY: PASS")
    print("PZAAS EIGHT BRANCHES: PASS")
    print("NEXT: FULL MODEL NUMERICAL PARITY")

except Exception:
    traceback.print_exc()
    print("PZAAS SEQUENCE PARITY: BLOCKED")

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY
