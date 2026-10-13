podman run --rm -i -v "$PWD:/workspace" -w /workspace --entrypoint python docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, types, inspect
from pathlib import Path
import numpy as np
import torch

# Same import-only FAISS workaround used for successful preprocessing.
sys.modules["faiss"] = types.ModuleType("faiss")

root = Path("artifacts/v1.168")
base = Path("artifacts/v1.168-max/cta_max")

sys.path.insert(0, str(root / "core-artifact"))
sys.path.insert(0, str(root / "utils/dependency-utils"))

from pipeline import pipeline

inputs = torch.load(
    base / "real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=True
)
assert isinstance(inputs, dict) and len(inputs) == 17

p = pipeline()
p.load()
print("ORIGINAL PIPELINE LOAD: PASS")

model = p.model_base
assert isinstance(model, torch.nn.Module)
model.eval()

signature = inspect.signature(model.forward)
kwargs = {k: v for k, v in inputs.items() if k in signature.parameters}

# Original DS input name versus GRecBase forward argument.
if "tasks_in" in signature.parameters and "task_in" in inputs:
    kwargs["tasks_in"] = inputs["task_in"]

missing = [
    k for k, v in signature.parameters.items()
    if k not in kwargs
    and v.default is inspect.Parameter.empty
    and k != "self"
]
assert not missing, f"Missing GRecBase inputs: {missing}"

with torch.inference_mode():
    result = model(**kwargs)

assert isinstance(result, torch.Tensor), type(result)
pt = result.detach().cpu().numpy()
mx = np.load(base / "real_sanity_max_output.npy")

print("PYTORCH:", pt.shape)
print("MAX:", mx.shape)

assert pt.shape == mx.shape == (1, 10819)

diff = np.abs(pt.astype(np.float64) - mx.astype(np.float64))
print("MEAN DIFF:", float(diff.mean()))
print("MAX DIFF:", float(diff.max()))
print("MATCH:", bool(np.allclose(pt, mx, rtol=1e-3, atol=1e-3)))

out = base / "real_sanity_pytorch_output.npy"
np.save(out, pt)
print("PYTORCH REFERENCE SAVED:", out)
print("ORIGINAL PYTORCH AND DS SOURCE UNCHANGED")
PY
