REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys, types, torch, numpy as np, traceback
from pathlib import Path

try:
    root = Path("artifacts/v1.113-max/maxserve_bplan_extension").resolve()
    dev = root / "bplan_max_dev"

    pkg = types.ModuleType("cta_max")
    pkg.__path__ = [str(dev)]
    sys.modules["cta_max"] = pkg
    sys.path.insert(0, str(dev))

    from max.driver import CPU
    from max.graph import DeviceRef
    from max.engine import InferenceSession
    from grecbase_fusion_full_head_72_max import (
        build_grecbase_fusion_graph_order_correct
    )

    state = torch.load(
        "artifacts/v1.113/core-artifact/base_model.pt",
        map_location="cpu", weights_only=True
    )
    if "state_dict" in state:
        state = state["state_dict"]

    registry = {}

    def register(name, value):
        if name in registry:
            assert np.array_equal(registry[name], value), (
                f"Conflicting weight: {name}"
            )
        else:
            registry[name] = value

    for name, tensor in state.items():
        if not isinstance(tensor, torch.Tensor):
            continue

        value = tensor.detach().cpu().contiguous().numpy()
        register(name, value)

        if name.endswith(".weight"):
            register(name[:-7], value)

        if name.startswith("sequence_transformer.ptransformer.") and ".fn." in name:
            alias = name.replace(".fn.", ".", 1)
            register(alias, value)
            if alias.endswith(".weight"):
                register(alias[:-7], value)

    device = CPU()
    graph = build_grecbase_fusion_graph_order_correct(
        DeviceRef.from_device(device)
    )

    assert len(graph.inputs) == 72
    print("BPLAN CORRECTED GRAPH: PASS", flush=True)

    session = InferenceSession(devices=[device])
    model = session.load(graph, weights_registry=registry)

    print("BPLAN CORRECTED CPU COMPILE: PASS", flush=True)
    print("ORIGINAL DS AND CTA: UNCHANGED")

except Exception:
    print("BPLAN CORRECTED CPU COMPILE: FAILED", flush=True)
    traceback.print_exc()
    sys.exit(1)
PY
