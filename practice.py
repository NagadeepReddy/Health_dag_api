podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import numpy as np
sys.path.insert(0, "artifacts/v1.168-max")
from cta_max.run_real_sanity_input_adapter import build_real_inputs

labels, arrays = build_real_inputs()
for i, (label, value) in enumerate(zip(labels, arrays)):
    if "valid" in label.lower() or "length" in label.lower() or "v1" in label.lower():
        a = np.asarray(value)
        print(i, label, "shape:", a.shape, "values:", a.ravel()[:20].tolist())
PY
