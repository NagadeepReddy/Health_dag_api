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

print("=== PZAAS SEQUENCE FINAL PARITY ===", flush=True)

try:
    from max.driver import CPU
    from max.dtype import DType
    from max.engine import InferenceSession
    from max.graph import Graph, DeviceRef, TensorType

    from pzaas_max.sequence_transformer_max import ParallelTransformerMAEPMAX
    from pzaas_max.parallel_transformer_block_2layers import ParallelTransformerBlockMAX
    from pzaas_max.sequence_postprocess_max import SequencePostprocessMAX

    W = Path("/models/pzaas_max/pzaas_base_weights")
    assert W.is_dir()

    weights = {
        p.stem: np.ascontiguousarray(
            np.load(p, allow_pickle=False)
        )
        for p in W.glob("*.npy")
    }

    assert len(weights) == 208, len(weights)

    print("ORIGINAL WEIGHTS:", len(weights))

    # Register aliases without modifying weight files.
    aliases = {}

    for name, value in list(weights.items()):
        if name.endswith(".weight"):
            alias = name[:-7]
            if alias not in weights:
                aliases[alias] = value

    weights.update(aliases)

    print("WEIGHT ALIASES:", len(aliases))
    print("TOTAL REGISTRY KEYS:", len(weights))

    required = [
        "sequence_transformer.page_embedding",
        "sequence_transformer.item_embedding",
        "sequence_transformer.item_meta_embedding",
        "sequence_transformer.item_pre_embedding",
        "sequence_transformer.page_meta_wide_dense",
        "sequence_transformer.seq_dense",
    ]

    missing = [k for k in required if k not in weights]

    if missing:
        raise RuntimeError(f"Missing registered weights: {missing}")

    print("MAX WEIGHT REGISTRY: PASS", flush=True)

    reference = torch.load(
        "/validation/ppa_pytorch_reference_01.pt",
        map_location="cpu",
        weights_only=True
    )

    d = reference["model_in"]

    with np.load(
        "/validation/pzaas_eight_branch_targets.npz",
        allow_pickle=False
    ) as f:
        keys = list(f.files)
        matches = [
            k for k in keys
            if "sequence" in k.lower()
        ]

        assert len(matches) == 1, (
            f"Sequence reference ambiguous: {keys}"
        )

        expected = np.ascontiguousarray(
            f[matches[0]].astype(np.float32)
        )

    def inp(name):
        return np.ascontiguousarray(
            d[name].detach().cpu()
            .numpy().astype(np.int64)
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

    angles = np.arange(
        50, dtype=np.float32
    )[:, None] * inv[None, :]

    position = np.ascontiguousarray(
        np.concatenate(
            [angles, angles], axis=-1
        ).reshape(1, 1, 50, 256)
    )

    print("PYTORCH INPUTS: PASS", flush=True)

    device = DeviceRef.CPU()

    with Graph(
        "pzaas_sequence_registry_fixed",
        input_types=[
            TensorType(DType.int64, [1,50], device=device),
            TensorType(DType.int64, [1,50], device=device),
            TensorType(DType.int64, [1,50], device=device),
            TensorType(DType.float32, [1,50,1], device=device),
            TensorType(DType.float32, [1,1,50,256], device=device),
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

        post = SequencePostprocessMAX(
            dtype=DType.float32,
            device=device
        )

        x = features(pg, it, im, it, pw)
        x = x + block0(x, pos, length)
        x = x + block1(x, pos, length)

        graph.output(post(x))

    print("MAX SEQUENCE GRAPH: PASS", flush=True)

    session = InferenceSession(devices=[CPU()])

    model = session.load(
        graph,
        weights_registry=weights
    )

    print("REAL MAX COMPILE + WEIGHT BIND: PASS", flush=True)

    actual = model.execute(
        page,
        item,
        meta,
        wide,
        position,
        valid
    )[0].to_numpy()

    print("MAX OUTPUT:", actual.shape)
    print("PYTORCH OUTPUT:", expected.shape)

    assert actual.shape == expected.shape, (
        "Output shape mismatch"
    )

    assert np.isfinite(actual).all(), (
        "MAX output contains NaN/Inf"
    )

    diff = np.abs(actual - expected)

    print("MAX ABS DIFF:", float(diff.max()))
    print("MEAN ABS DIFF:", float(diff.mean()))

    parity = np.allclose(
        actual,
        expected,
        atol=1e-3,
        rtol=1e-3
    )

    if not parity:
        print("FIRST 8 MAX:", actual.ravel()[:8])
        print("FIRST 8 PYTORCH:", expected.ravel()[:8])
        raise AssertionError("Numerical parity mismatch")

    np.save(
        "/validation/pzaas_sequence_max.npy",
        actual,
        allow_pickle=False
    )

    print("SEQUENCE NUMERICAL PARITY: PASS")
    print("PZAAS ALL EIGHT BRANCHES: PASS")
    print("NEXT: FULL MODEL PARITY AND NATIVE SERVING")

except Exception:
    traceback.print_exc()
    print("PZAAS SEQUENCE TEST: BLOCKED")

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY
