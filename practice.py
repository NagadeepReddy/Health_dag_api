REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" \
  -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys, torch, traceback
from pathlib import Path

root = Path("artifacts/v1.113-max/maxserve_bplan_extension").resolve()
sys.path.insert(0, str(root / "bplan_max_dev"))

try:
    from run_real_sanity_input_adapter import build_real_inputs

    saved = torch.load(
        root / "bplan_neural_inputs.pt",
        map_location="cpu",
        weights_only=True
    )
    assert isinstance(saved, dict)

    data = dict(saved)
    if "task_in" not in data and "tasks_in" in data:
        data["task_in"] = data["tasks_in"]

    labels, arrays = build_real_inputs(model_in=data)
    assert len(labels) == len(arrays) == 72

    print("BPLAN REAL MAX INPUT MAPPING: PASS")
    print("INPUT COUNT:", len(arrays))
except Exception:
    print("BPLAN REAL MAX INPUT MAPPING: FAILED")
    traceback.print_exc()
    sys.exit(1)
PY
