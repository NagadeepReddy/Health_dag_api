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
import traceback
from pathlib import Path
import numpy as np
import torch
from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType, ops
from pzaas_max import grecbase_fusion_full_head_72_max as m

print("=== PZAAS SIBLING OUTPUT DIAGNOSTIC ===", flush=True)

try:
    ref = torch.load(
        "/validation/ppa_pytorch_reference_01.pt",
        map_location="cpu", weights_only=True
    )
    d = ref["model_in"]

    with np.load(
        "/validation/pzaas_eight_branch_targets.npz",
        allow_pickle=False
    ) as f:
        expected = f["sibling"].astype(np.float32)

    deep = d["sibling_deep_in"]
    wide = d["sibling_wide_in"]
    valid = d["sibling_vl_in"]

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

    print("VALID SIBLING COUNT:", valid.tolist(), flush=True)

    device = DeviceRef.CPU()

    with Graph(
        "pzaas_sibling_diagnostic",
        input_types=[
            TensorType(DType.int64, s, device=device)
            for s in shapes
        ]
    ) as graph:

        inp = graph.inputs
        siblings = []

        for i in range(10):
            p = inp[i*4:(i+1)*4]
            x = m.sibling_context_forward(
                p[:3], p[3], device
            )
            siblings.append(
                ops.reshape(x, [1, 1, 128])
            )

        stack = ops.concat(siblings, axis=1)

        length = ops.cast(
            ops.reshape(inp[40], [1, 1]),
            DType.float32
        )

        epsilon = ops.constant(
            np.array(1e-7, dtype=np.float32),
            dtype=DType.float32,
            device=device
        )

        mean = ops.sum(stack, axis=1) / (
            length + epsilon
        )
        maximum = ops.max(stack, axis=1)

        graph.output(
            ops.concat([mean, maximum], axis=1)
        )

    print("MAX GRAPH: PASS", flush=True)

    weights = {
        p.stem: np.ascontiguousarray(
            np.load(p, allow_pickle=False)
        )
        for p in Path(m.WDIR).glob("*.npy")
    }

    session = InferenceSession(devices=[CPU()])
    model = session.load(
        graph, weights_registry=weights
    )

    print("MAX CPU COMPILATION: PASS", flush=True)

    actual = model.execute(*values)[0].to_numpy()

    print("ACTUAL SHAPE:", actual.shape)
    print("EXPECTED SHAPE:", expected.shape)
    print("ACTUAL DTYPE:", actual.dtype)
    print("EXPECTED DTYPE:", expected.dtype)

    print("ACTUAL FINITE:", bool(np.isfinite(actual).all()))
    print("EXPECTED FINITE:", bool(np.isfinite(expected).all()))
    print("NAN COUNT:", int(np.isnan(actual).sum()))
    print("INF COUNT:", int(np.isinf(actual).sum()))

    finite = actual[np.isfinite(actual)]

    if finite.size:
        print("ACTUAL FINITE MIN:", float(finite.min()))
        print("ACTUAL FINITE MAX:", float(finite.max()))

    if actual.shape != expected.shape:
        print("FAILURE: OUTPUT SHAPE MISMATCH")
    elif not np.isfinite(actual).all():
        print("FAILURE: NON-FINITE MAX OUTPUT")
    else:
        diff = np.abs(actual - expected)
        print("MAX ABS DIFF:", float(diff.max()))
        print("MEAN ABS DIFF:", float(diff.mean()))

        passed = np.allclose(
            actual, expected,
            atol=1e-3, rtol=1e-3
        )

        print(
            "SIBLING PARITY:",
            "PASS" if passed else "FAILED"
        )

        if passed:
            np.save(
                "/validation/pzaas_sibling_max.npy",
                actual, allow_pickle=False
            )
            print("REMAINING FOUR BRANCHES: NEXT")

    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    print("DIAGNOSTIC: COMPLETE")

except Exception:
    traceback.print_exc()
    raise SystemExit("SIBLING DIAGNOSTIC: BLOCKED")
PY
