REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" \
  -v /bplan_out:/bplan_out:ro \
  -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys, torch, traceback
from pathlib import Path

dev = Path("artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev").resolve()
sys.path.insert(0, str(dev))

try:
    from run_real_sanity_input_adapter import build_real_inputs

    saved = torch.load(
        "/bplan_out/bplan_neural_inputs.pt",
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
    print("ORIGINAL DS AND CTA: UNCHANGED")

except Exception:
    print("BPLAN REAL MAX INPUT MAPPING: FAILED")
    traceback.print_exc()
    sys.exit(1)
PY
