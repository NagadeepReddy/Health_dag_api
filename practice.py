REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys, types, torch, traceback
from pathlib import Path

try:
    root = Path("artifacts/v1.113-max/maxserve_bplan_extension").resolve()
    dev = root / "bplan_max_dev"

    # Temporary BPLAN-local import compatibility.
    pkg = types.ModuleType("cta_max")
    pkg.__path__ = [str(dev)]
    sys.modules["cta_max"] = pkg
    sys.path.insert(0, str(dev))

    from max.driver import CPU
    from max.graph import DeviceRef
    from grecbase_fusion_full_head_72_max import build_grecbase_fusion_graph_order_correct
    from run_real_sanity_input_adapter import build_real_inputs

    data = torch.load(root / "bplan_neural_inputs.pt",
                      map_location="cpu", weights_only=True)

    if "task_in" not in data and "tasks_in" in data:
        data = {**data, "task_in": data["tasks_in"]}

    labels, arrays = build_real_inputs(model_in=data)
    graph = build_grecbase_fusion_graph_order_correct(
        DeviceRef.from_device(CPU())
    )

    assert len(labels) == len(arrays) == len(graph.inputs) == 72

    mismatches = []
    for i, (label, array, inp) in enumerate(
        zip(labels, arrays, graph.inputs)
    ):
        actual = tuple(array.shape)
        expected = tuple(int(x) for x in inp.type.shape)
        if actual != expected:
            mismatches.append((i, label, actual, expected))

    for item in mismatches:
        print("MISMATCH:", item)

    assert not mismatches, f"{len(mismatches)} input mismatches"

    print("BPLAN REAL MAX INPUTS: PASS (72/72)")
    print("ORIGINAL DS AND CTA: UNCHANGED")

except Exception:
    print("BPLAN REAL MAX INPUTS: FAILED")
    traceback.print_exc()
    sys.exit(1)
PY
