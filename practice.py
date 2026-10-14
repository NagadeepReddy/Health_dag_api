podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, torch, numpy as np
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
sys.path.insert(0, str(base))

from run_real_sanity_input_adapter import build_real_inputs

data = torch.load(base/"real_sanity_model_in.pt",
                  map_location="cpu", weights_only=True)
labels, arrays = build_real_inputs(model_in=data)

print("=== ORIGINAL FIRST VALID SIBLING ===")
for key in ("sibling_deep_in", "sibling_wide_in", "sibling_v1_in"):
    x = data[key].detach().cpu().numpy()
    print(key, "shape:", x.shape,
          "first:", x[..., 0].ravel()[:8].tolist())

print("\n=== MAX MAPPED SIBLING INPUTS ===")
matches = [(i, str(label), np.asarray(arr))
           for i, (label, arr) in enumerate(zip(labels, arrays))
           if "sibling" in str(label).lower()]

print("Mapped sibling entries:", len(matches))
for i, label, arr in matches[:8]:
    print(i, label, arr.shape, arr.ravel()[:8].tolist())
PY
