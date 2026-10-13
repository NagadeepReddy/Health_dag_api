podman run --rm -i -v "$PWD:/workspace" -w /workspace --entrypoint python docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, types, importlib.machinery, inspect
from pathlib import Path
import numpy as np
import torch

# Import-only FAISS stub compatible with Transformers find_spec().
faiss = types.ModuleType("faiss")
faiss.__spec__ = importlib.machinery.ModuleSpec("faiss", loader=None)
sys.modules["faiss"] = faiss

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

model = p.model_base.cpu().eval()
signature = inspect.signature(model.forward)

kwargs = {
    k: v for k, v in inputs.items()
    if k in signature.parameters
}
if "tasks_in" in signature.parameters and "task_in" in inputs:
    kwargs["tasks_in"] = inputs["task_in"]

missing = [
    k for k, v in signature.parameters.items()
    if k != "self"
    and k not in kwargs
    and v.default is inspect.Parameter.empty
]
assert not missing, f"Missing inputs: {missing}"

with torch.inference_mode():
    result = model(**kwargs)

assert isinstance(result, torch.Tensor), type(result)
pt = result.detach().cpu().numpy().astype(np.float32)
mx = np.load(base / "real_sanity_max_output.npy").astype(np.float32)

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
print("ORIGINAL DS CODE UNCHANGED")
PY
