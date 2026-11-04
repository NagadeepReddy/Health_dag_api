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
import traceback
from pathlib import Path
import numpy as np
import torch

from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType, ops

from pzaas_max import grecbase_fusion_full_head_72_max as m

print("=== PZAAS REAL MAX AUX BRANCH PARITY ===", flush=True)

try:
    ref = torch.load(
        "/validation/ppa_pytorch_reference_01.pt",
        map_location="cpu",
        weights_only=True
    )
    model_in = ref["model_in"]

    with np.load(
        "/validation/pzaas_eight_branch_targets.npz",
        allow_pickle=False
    ) as data:
        names = ["task", "ihq", "jet"]
        expected = np.stack(
            [data[name] for name in names],
            axis=1
        ).astype(np.float32)

    assert expected.shape == (1, 3, 256)

    def to_numpy(t):
        return np.ascontiguousarray(
            t.detach().cpu().numpy().astype(np.int64)
        )

    inputs = [
        to_numpy(model_in["task_in"][0]),
        to_numpy(model_in["task_in"][1]),
        to_numpy(model_in["ihq_in"]),
        to_numpy(model_in["jet_name_in"]),
        to_numpy(model_in["jet_status_in"])
    ]

    shapes = [
        [1], [1], [1, 50], [1, 50], [1, 50]
    ]

    for value, shape in zip(inputs, shapes):
        assert list(value.shape) == shape

    print("PYTORCH AUX INPUTS: PASS", flush=True)

    device = DeviceRef.CPU()

    with Graph(
        "pzaas_aux_branches_real",
        input_types=[
            TensorType(DType.int64, shape, device=device)
            for shape in shapes
        ]
    ) as graph:

        task0, task1, ihq_ids, jet_name, jet_status = graph.inputs

        task, ihq, jet = m.grecbase_aux_features(
            task0, task1, ihq_ids,
            jet_name, jet_status, device
        )

        packed = ops.concat(
            [
                ops.reshape(x, [1, 1, 256])
                for x in (task, ihq, jet)
            ],
            axis=1
        )

        graph.output(packed)

    print("MAX AUX GRAPH BUILD: PASS", flush=True)

    weights = {}
    for path in sorted(Path(m.WDIR).glob("*.npy")):
        weights[path.stem] = np.ascontiguousarray(
            np.load(path, allow_pickle=False)
        )

    print("AVAILABLE MAX WEIGHTS:", len(weights), flush=True)

    session = InferenceSession(devices=[CPU()])
    model = session.load(
        graph,
        weights_registry=weights
    )

    print("REAL MAX AUX CPU COMPILATION: PASS", flush=True)

    actual = model.execute(*inputs)[0].to_numpy()

    assert actual.shape == expected.shape
    assert np.isfinite(actual).all()

    all_pass = True

    for i, name in enumerate(names):
        diff = np.abs(actual[:, i] - expected[:, i])
        ok = np.allclose(
            actual[:, i],
            expected[:, i],
            atol=1e-3,
            rtol=1e-3
        )
        all_pass &= ok

        print(
            name.upper(),
            "MAX ABS DIFF:", float(diff.max()),
            "PARITY:", "PASS" if ok else "FAILED",
            flush=True
        )

    print(
        "PZAAS THREE BRANCH PARITY:",
        "PASS" if all_pass else "FAILED"
    )
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")

    if not all_pass:
        raise SystemExit(1)

    print("REMAINING FIVE BRANCHES: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS AUX BRANCH TEST: BLOCKED")
PY
