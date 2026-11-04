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
import numpy as np
import torch
import traceback
from pathlib import Path
from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType, ops
from pzaas_max import grecbase_fusion_full_head_72_max as m

print("=== PZAAS REAL MAX SIBLING PARITY RETRY ===", flush=True)

try:
    ref = torch.load(
        "/validation/ppa_pytorch_reference_01.pt",
        map_location="cpu", weights_only=True
    )
    d = ref["model_in"]

    with np.load(
        "/validation/pzaas_eight_branch_targets.npz"
    ) as f:
        expected = f["sibling"].astype(np.float32)

    deep = d["sibling_deep_in"]
    wide = d["sibling_wide_in"]
    valid = d["sibling_vl_in"]

    assert deep.shape == (1, 3, 10)
    assert wide.shape == (1, 18, 10)
    assert valid.shape == (1,)
    assert expected.shape == (1, 256)

    values, shapes = [], []

    for i in range(10):
        for j in range(3):
            values.append(np.ascontiguousarray(
                deep[:, j, i].numpy().astype(np.int64)
            ))
            shapes.append([1])

        values.append(np.ascontiguousarray(
            wide[:, :, i].numpy().astype(np.int64)
        ))
        shapes.append([1, 18])

    values.append(np.ascontiguousarray(
        valid.numpy().astype(np.int64)
    ))
    shapes.append([1])

    print("SIBLING INPUT MAPPING: PASS", flush=True)

    device = DeviceRef.CPU()

    with Graph(
        "pzaas_sibling_fixed",
        input_types=[
            TensorType(DType.int64, s, device=device)
            for s in shapes
        ]
    ) as graph:
        inputs = graph.inputs
        siblings = []

        for i in range(10):
            part = inputs[i*4:(i+1)*4]
            x = m.sibling_context_forward(
                part[:3], part[3], device
            )
            siblings.append(ops.reshape(x, [1, 1, 128]))

        stack = ops.concat(siblings, axis=1)

        length = ops.cast(
            ops.reshape(inputs[40], [1, 1]),
            DType.float32
        )

        mean = ops.sum(stack, axis=1) / (
            length + ops.constant(
                np.array(1e-7, dtype=np.float32),
                dtype=DType.float32,
                device=device
            )
        )

        maximum = ops.max(stack, axis=1)
        graph.output(ops.concat([mean, maximum], axis=1))

    print("MAX SIBLING GRAPH: PASS", flush=True)

    weights = {
        p.stem: np.ascontiguousarray(
            np.load(p, allow_pickle=False)
        )
        for p in Path(m.WDIR).glob("*.npy")
    }
    assert len(weights) == 208

    session = InferenceSession(devices=[CPU()])
    model = session.load(graph, weights_registry=weights)

    print("REAL MAX CPU COMPILATION: PASS", flush=True)

    actual = model.execute(*values)[0].to_numpy()

    assert actual.shape == expected.shape
    assert np.isfinite(actual).all()

    diff = np.abs(actual - expected)
    passed = np.allclose(
        actual, expected, atol=1e-3, rtol=1e-3
    )

    print("MAX OUTPUT:", actual.shape)
    print("PYTORCH OUTPUT:", expected.shape)
    print("MAX ABS DIFF:", float(diff.max()))
    print("MEAN ABS DIFF:", float(diff.mean()))
    print("SIBLING PARITY:", "PASS" if passed else "FAILED")
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")

    if not passed:
        raise SystemExit(1)

    print("REMAINING FOUR BRANCHES: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS SIBLING PARITY: BLOCKED")
PY
