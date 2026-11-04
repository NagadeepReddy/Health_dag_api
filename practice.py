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
-e XDG_CACHE_HOME=/tmp/cache \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/models \
-v "$M:/models:ro" \
-v "$V:/validation:rw" \
-w /models \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import traceback
import numpy as np
import torch
from pathlib import Path

print("=== PZAAS SEQUENCE WEIGHT FIX + PARITY ===", flush=True)

try:
    from max.driver import CPU
    from max.dtype import DType
    from max.engine import InferenceSession
    from max.graph import Graph, DeviceRef, TensorType

    from pzaas_max.sequence_transformer_max import ParallelTransformerMAEPMAX
    from pzaas_max.parallel_transformer_block_2layers import ParallelTransformerBlockMAX
    from pzaas_max.sequence_postprocess_max import SequencePostprocessMAX

    root = Path("/models/pzaas_max/pzaas_base_weights")
    assert root.is_dir(), root

    original = {
        p.stem: np.ascontiguousarray(np.load(p, allow_pickle=False))
        for p in root.glob("*.npy")
    }

    assert len(original) == 208, len(original)

    weights = dict(original)

    # Build compatible names without changing trained weights.
    for name, array in original.items():
        variants = {
            name,
            name.replace(".fn.", "."),
        }

        for key in list(variants):
            if key.endswith(".weight"):
                variants.add(key[:-7])

        for key in variants:
            if key in weights:
                if not np.array_equal(weights[key], array):
                    raise ValueError(f"Alias conflict: {key}")
            else:
                weights[key] = array

    print("ORIGINAL WEIGHTS:", len(original))
    print("TOTAL REGISTRY KEYS:", len(weights))

    required = [
        "sequence_transformer.page_embedding",
        "sequence_transformer.item_embedding",
        "sequence_transformer.item_meta_embedding",
        "sequence_transformer.item_pre_embedding",
        "sequence_transformer.ptransformer.0.fused_attn_ff_proj.weight",
        "sequence_transformer.ptransformer.1.fused_attn_ff_proj.weight",
    ]

    missing = [x for x in required if x not in weights]
    assert not missing, f"Missing names: {missing}"

    print("WEIGHT REGISTRY FIX: PASS", flush=True)

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
        keys = [k for k in f.files if "sequence" in k.lower()]
        assert len(keys) == 1, f"Sequence target keys: {f.files}"
        expected = np.ascontiguousarray(
            f[keys[0]].astype(np.float32)
        )

    def tensor(name):
        return np.ascontiguousarray(
            d[name].detach().cpu().numpy().astype(np.int64)
        )

    page = tensor("page_in")
    item = tensor("item_in")
    meta = tensor("item_meta_in")
    length = tensor("vl_in")

    wide = np.ascontiguousarray(
        d["page_meta_wide_in"][0]
        .detach().cpu().numpy()
        .astype(np.float32)
        .reshape(1, 50, 1)
    )

    inv = original[
        "sequence_transformer.ptransformer.0.fn.rotary_emb.inv_freq"
    ].astype(np.float32)

    angles = np.arange(50, dtype=np.float32)[:, None] * inv[None, :]
    position = np.ascontiguousarray(
        np.concatenate([angles, angles], axis=-1)
        .reshape(1, 1, 50, 256)
    )

    device = DeviceRef.CPU()

    with Graph(
        "pzaas_sequence_fixed_registry",
        input_types=[
            TensorType(DType.int64, [1, 50], device=device),
            TensorType(DType.int64, [1, 50], device=device),
            TensorType(DType.int64, [1, 50], device=device),
            TensorType(DType.float32, [1, 50, 1], device=device),
            TensorType(DType.float32, [1, 1, 50, 256], device=device),
            TensorType(DType.int64, [1], device=device),
        ]
    ) as graph:

        pg, it, im, pw, pos, valid = graph.inputs

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
        x = x + block0(x, pos, valid)
        x = x + block1(x, pos, valid)

        graph.output(post(x))

    print("MAX GRAPH: PASS", flush=True)

    model = InferenceSession(devices=[CPU()]).load(
        graph,
        weights_registry=weights
    )

    print("MAX COMPILATION + WEIGHT BINDING: PASS", flush=True)

    actual = model.execute(
        page, item, meta, wide, position, length
    )[0].to_numpy()

    print("MAX SHAPE:", actual.shape)
    print("PYTORCH SHAPE:", expected.shape)

    assert actual.shape == expected.shape
    assert np.isfinite(actual).all()

    diff = np.abs(actual - expected)

    print("MAX ABS DIFF:", float(diff.max()))
    print("MEAN ABS DIFF:", float(diff.mean()))

    if np.allclose(actual, expected, atol=1e-3, rtol=1e-3):
        np.save(
            "/validation/pzaas_sequence_max.npy",
            actual,
            allow_pickle=False
        )
        print("PZAAS SEQUENCE PARITY: PASS")
        print("NEXT: FULL MODEL PARITY")
    else:
        print("PZAAS SEQUENCE NUMERICAL PARITY: FAIL")
        print("FIRST MAX VALUES:", actual.ravel()[:8])
        print("FIRST PYTORCH VALUES:", expected.ravel()[:8])

except Exception:
    traceback.print_exc()
    print("PZAAS SEQUENCE TEST: BLOCKED")

print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY
