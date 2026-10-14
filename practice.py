podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, torch, numpy as np
from pathlib import Path

b = Path("artifacts/v1.168-max/cta_max")
sys.path.insert(0, str(b))
from run_real_sanity_input_adapter import build_real_inputs

data = torch.load(b/"real_sanity_model_in.pt",
                  map_location="cpu", weights_only=True)
labels, arrays = build_real_inputs(model_in=data)

print("=== SIBLING ADAPTER MAPPING ===")
for i, (label, value) in enumerate(zip(labels, arrays)):
    if "sibling" in str(label).lower() or i in range(65, 69):
        a = np.asarray(value)
        print(i, label, "shape:", a.shape,
              "first:", a.ravel()[:8].tolist())
PY
