cd /application1/sajjna8/rt-pzaas-v1.0 && \
M="$PWD/artifacts/v1.472-max" && \
V="$M/pzaas_max/validation" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 10g --tmpfs /tmp:rw,size=1g \
-e HOME=/tmp \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/models \
-v "$M:/models:ro" \
-v "$V:/validation:ro" \
-w /models \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import traceback
import numpy as np

from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType, ops

print("=== PZAAS REAL MAX FUSION RETRY ===", flush=True)

try:
    from pzaas_max import grecbase_fusion_full_head_72_max as m

    print("PZAAS PACKAGE IMPORT: PASS", flush=True)

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

    def norm(x, name):
        weight = np.load(
            m.WDIR / (name + ".g.npy"),
            allow_pickle=False
        ).astype(np.float32)

        assert weight.shape == (256,)

        gamma = ops.constant(
            weight, dtype=DType.float32, device=device
        )

        variance = ops.reshape(
            ops.mean(x * x, axis=-1), [1, 8, 1]
        )

        return x * ops.rsqrt(variance + 1e-6) * gamma

    inv = np.load(
        m.WDIR / "att_pooling.rotary_emb.inv_freq.npy",
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
        "pzaas_real_fusion",
        input_types=(
            TensorType(
                DType.float32,
                [1, 8, 256],
                device=device
            ),
        )
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
    model = session.load(graph)

    print("REAL MAX CPU COMPILATION: PASS", flush=True)

    outputs = model.execute(fusion)
    result = outputs[0].to_numpy()

    assert result.shape == reference.shape
    assert np.isfinite(result).all()
    assert np.isfinite(reference).all()

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
        "PZAAS REAL MAX FUSION PARITY:",
        "PASS" if parity else "FAILED"
    )

    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")

    if not parity:
        raise SystemExit(1)

    print("FULL PZAAS MAX PARITY: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS FUSION RETRY: BLOCKED")
PY
