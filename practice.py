ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

ROOT="$ROOT" python3 - <<'PY'
import os, sys, torch, traceback
from pathlib import Path

sys.path.insert(0, os.environ["ROOT"])
from run_real_sanity_input_adapter import build_real_inputs

try:
    saved = torch.load(
        "/bplan_out/bplan_neural_inputs.pt",
        map_location="cpu",
        weights_only=True
    )
    assert isinstance(saved, dict)

    print("BPLAN SAVED INPUT KEYS:", sorted(saved), flush=True)

    # Translate the verified BPLAN naming difference in memory only.
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
