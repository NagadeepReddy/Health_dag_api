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
import numpy as np
import torch
import traceback
from pathlib import Path
from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType
from pzaas_max import grecbase_fusion_full_head_72_max as m

print("=== PZAAS SEARCH0 + SEARCH1 REAL MAX ===", flush=True)

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
        expected0 = f["search0"].astype(np.float32)
        expected1 = f["search1"].astype(np.float32)

    ids = np.ascontiguousarray(
        d["input_ids"].numpy().astype(np.int64)
    )
    mask = np.ascontiguousarray(
        d["attention_mask"].numpy().astype(np.int64)
    )

    assert ids.shape == mask.shape == (1, 5)
    assert expected0.shape == expected1.shape == (1, 256)
    print("SEARCH INPUT MAPPING: PASS", flush=True)

    device = DeviceRef.CPU()

    with Graph(
        "pzaas_search_branches",
        input_types=[
            TensorType(DType.int64, [1, 5], device=device),
            TensorType(DType.int64, [1, 5], device=device)
        ]
    ) as graph:
        search = m.nlp_bert_forward(
            graph.inputs[0],
            graph.inputs[1],
            device,
            5
        )
        graph.output(search)

    print("SEARCH MAX GRAPH: PASS", flush=True)

    weights = {
        p.stem: np.ascontiguousarray(
            np.load(p, allow_pickle=False)
        )
        for p in Path(m.WDIR).glob("*.npy")
    }
    assert len(weights) == 208

    session = InferenceSession(devices=[CPU()])
    model = session.load(
        graph, weights_registry=weights
    )
    print("SEARCH MAX CPU COMPILATION: PASS", flush=True)

    output = model.execute(ids, mask)[0].to_numpy()
    assert output.shape == (1, 512)
    assert np.isfinite(output).all()

    actual0 = output[:, :256]
    actual1 = output[:, 256:]

    results = []
    for name, actual, expected in [
        ("SEARCH0", actual0, expected0),
        ("SEARCH1", actual1, expected1)
    ]:
        diff = np.abs(actual - expected)
        passed = np.allclose(
            actual, expected, atol=1e-3, rtol=1e-3
        )
        print(name, "MAX ABS DIFF:", float(diff.max()))
        print(name, "MEAN ABS DIFF:", float(diff.mean()))
        print(name, "PARITY:", "PASS" if passed else "FAILED")
        results.append(passed)

    if not all(results):
        raise SystemExit("SEARCH NUMERICAL PARITY: FAILED")

    np.save("/validation/pzaas_search0_max.npy", actual0)
    np.save("/validation/pzaas_search1_max.npy", actual1)

    print("SEARCH0 + SEARCH1: PASS")
    print("ORIGINAL DS: UNCHANGED")
    print("CTA / BPLAN: UNCHANGED")
    print("REMAINING: SEQUENCE + CONTEXT")
    print("FULL MAX PARITY + NATIVE HTTP: NEXT")

except Exception:
    traceback.print_exc()
    raise SystemExit("PZAAS SEARCH TEST: BLOCKED")
PY
