podman run --rm -i -v "$PWD:/workspace" -w /workspace --entrypoint python docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
from pathlib import Path
import numpy as np
import torch

root = Path("artifacts/v1.168")
base = Path("artifacts/v1.168-max/cta_max")

sys.path.insert(0, str(root / "core-artifact"))
sys.path.insert(0, str(root / "utils/dependency-utils"))

from pipeline import pipeline

inputs_path = base / "real_sanity_model_in.pt"
max_path = base / "real_sanity_max_output.npy"

assert inputs_path.is_file(), f"Missing: {inputs_path}"
assert max_path.is_file(), f"Missing: {max_path}"

model_inputs = torch.load(
    inputs_path, map_location="cpu", weights_only=True
)
assert isinstance(model_inputs, dict) and len(model_inputs) == 17

p = pipeline()
p.load()

candidates = []
for attr, value in vars(p).items():
    if isinstance(value, torch.nn.Module):
        for name, module in value.named_modules():
            if type(module).__name__ == "GRecBase":
                candidates.append((attr, name, module))

print("ORIGINAL GRecBase CANDIDATES:", len(candidates))
for attr, name, _ in candidates:
    print(" ", attr, name)

assert len(candidates) == 1, (
    "Need to identify the original base model safely"
)

model = candidates[0][2].cpu().eval()

with torch.inference_mode():
    result = model(**model_inputs)

assert isinstance(result, torch.Tensor)
pt = result.detach().cpu().numpy().astype(np.float32)
mx = np.load(max_path).astype(np.float32)

print("PYTORCH SHAPE:", pt.shape)
print("MAX SHAPE:", mx.shape)
assert pt.shape == mx.shape == (1, 10819)

diff = np.abs(pt.astype(np.float64) - mx.astype(np.float64))
print("MEAN DIFF:", float(diff.mean()))
print("MAX DIFF:", float(diff.max()))
print("MATCH:", bool(np.allclose(pt, mx, rtol=1e-3, atol=1e-3)))

output = base / "real_sanity_pytorch_output.npy"
np.save(output, pt)
print("PYTORCH REFERENCE SAVED:", output)
print("ORIGINAL PYTORCH AND DS SOURCE UNCHANGED")
PY
