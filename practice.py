REPO=/application1/sajjna8/rt-pzai-bplan-v1
DEV="$REPO/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev"

DEV="$DEV" python3 - <<'PY'
import os
from pathlib import Path

p = Path(os.environ["DEV"]) / "bplan_max_model_adapter.py"
s = p.read_text()
original = s

# Fix the BPLAN checkpoint path.
start = '        checkpoint_root = self.root.parents[1] / "v1.113" / "core-artifact"'
end = '        checkpoint_root = self.root.parents[3] / "v1.113" / "core-artifact"'

assert start in s and end in s, "STOP: unexpected adapter version"

s = s.replace(start + "\n", "")
s = s.replace(
    end,
    '        checkpoint_root = self.root.parents[2] / "v1.113" / "core-artifact"'
)

# Support the original DS naming of tasks_in.
old = '        labels, arrays = self.build_inputs(model_in=model_inputs)'
new = '''        model_inputs = dict(model_inputs)
        if "task_in" not in model_inputs and "tasks_in" in model_inputs:
            model_inputs["task_in"] = model_inputs["tasks_in"]
        labels, arrays = self.build_inputs(model_in=model_inputs)'''

assert old in s, "STOP: input adapter location changed"
s = s.replace(old, new)

p.write_text(s)
print("BPLAN CHECKPOINT PATH AND INPUT ALIAS: FIXED")
PY

python3 -m py_compile "$DEV/bplan_max_model_adapter.py" || exit 1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys
from pathlib import Path
import numpy as np
import torch

root = Path("artifacts/v1.113-max/maxserve_bplan_extension").resolve()
sys.path.insert(0, str(root / "bplan_max_dev"))

from bplan_max_model_adapter import BPlanMAXModel

print("LOADING BPLAN MAX ADAPTER...", flush=True)
model = BPlanMAXModel()
print("BPLAN MAX ADAPTER LOAD: PASS", flush=True)

inputs = torch.load(
    root / "bplan_neural_inputs.pt",
    map_location="cpu",
    weights_only=True
)

print("EXECUTING BPLAN MAX ADAPTER...", flush=True)
actual = model(**inputs).detach().numpy()

expected = torch.load(
    root / "bplan_pytorch_neural_output.pt",
    map_location="cpu",
    weights_only=True
).detach().numpy()

assert actual.shape == expected.shape == (1, 10438)

diff = float(np.max(np.abs(actual - expected)))
print("MAX ABS DIFFERENCE:", diff)

assert np.allclose(actual, expected, rtol=1e-3, atol=1e-4), \
    "STOP: BPLAN parity failed"

print("BPLAN MAX ADAPTER REAL INFERENCE: PASS")
print("BPLAN NUMERICAL PARITY: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
