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
-v "$V:/validation:ro" \
-w /models \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import numpy as np
import traceback

from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType, ops

from pzaas_max import grecbase_fusion_full_head_72_max as m

print("=== PZAAS REAL MAX FUSION PARITY ===", flush=True)

try:
    wdir = m.WDIR

    specs = {
        "att_pooling.fused_attn_ff_proj.weight": (2816, 256),
        "att_pooling.attn_out.weight": (256, 256),
        "att_pooling.ff_out.1.weight": (256, 1024),
    }

    registry = {}

    for name, shape in specs.items():
        weight = np.load(
            wdir / (name + ".npy"),
            allow_pickle=False
        )
        assert weight.shape == shape, (name, weight.shape)
        registry[name] = np.ascontiguousarray(
            weight.astype(np.float32)
        )
        print("BOUND:", name, shape, flush=True)

    print("MAX WEIGHT REGISTRY: PASS", flush=True)

    fusion = np.load(
        "/validation/pzaas_fusion_input.npy",
        allow_pickle=False
    ).astype(np.float32)

    reference = np.load(
        "/validation/pzaas_get_path_input.npy",
        allow_pickle=False
    ).astype(np.float32)

    assert fusion.shape == (1, 8, 256)
    assert reference.shape == (1, 2048)

    device = DeviceRef.CPU()

    def constant_weight(name, shape):
        value = np.load(
            wdir / (name + ".npy"),
            allow_pickle=False
        ).astype(np.float32)
        assert value.shape == shape
        return ops.constant(
            value, dtype=DType.float32, device=device
        )

    def norm(x, name):
        gamma = constant_weight(name + ".g", (256,))
        variance = ops.reshape(
            ops.mean(x * x, axis=-1), [1, 8, 1]
        )
        return x * ops.rsqrt(variance + 1e-6) * gamma

    inv = np.load(
        wdir / "att_pooling.rotary_emb.inv_freq.npy",
        allow_pickle=False
    ).astype(np.float32)

    assert inv.shape == (128,)

    angles = np.arange(
        8, dtype=np.float32
    )[:, None] * inv[None, :]

    position = np.concatenate(
        [angles, angles], axis=1
    )[None, None, :, :].astype(np.float32)

    with Graph(
        "pzaas_real_fusion_bound",
        input_types=[
            TensorType(
                DType.float32,
                [1, 8, 256],
                device=device
            )
        ]
    ) as graph:
        x = graph.inputs[0]

        x = norm(x, "moe_norm1")

        pos = ops.constant(
            position,
            dtype=DType.float32,
            device=device
        )

        block = m.AttPoolingBlockMAX(
            dtype=DType.float32,
            device=device,
            layer_idx=0
        )

        x = block(x, pos)
        x = norm(x, "moe_norm2")
        x = ops.reshape(x, [1, 2048])

        graph.output(x)

    print("MAX FUSION GRAPH: PASS", flush=True)

    session = InferenceSession(devices=[CPU()])

    model = session.load(
        graph,
        weights_registry=registry
    )

    print("REAL MAX CPU LOAD: PASS", flush=True)

    result = model.execute(fusion)[0].to_numpy()

    assert result.shape == reference.shape
    assert np.isfinite(result).all()

    diff = np.abs(result - reference)

    print("MAX OUTPUT:", result.shape)
    print("PYTORCH OUTPUT:", reference.shape)
    print("MAX ABS DIFF:", float(diff.max()))
    print("MEAN ABS DIFF:", float(diff.mean()))

    parity = np.allclose(
        result, reference,
        atol=1e-3,
        rtol=1e-3
    )

    print(
        "PZAAS MAX FUSION PARITY:",
        "PASS" if parity else "FAILED"
    )
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")

    if not parity:
        raise SystemExit(1)

    print("FULL PZAAS GRAPH PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS MAX FUSION: BLOCKED")
PY
