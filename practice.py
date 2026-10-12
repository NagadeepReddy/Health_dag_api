podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, ast, types, importlib.util, importlib.machinery
from pathlib import Path
import numpy as np
import torch

root = Path("/workspace/artifacts/v1.168")
base = Path("/workspace/artifacts/v1.168-max/cta_max")
source = root / "core-artifact/pipeline.py"

data = torch.load(
    base / "real_sanity_model_in.pt",
    map_location="cpu", weights_only=True
)
assert len(data) == 17

try:
    import faiss
except ImportError:
    guard = types.ModuleType("faiss")
    guard.__file__ = "<faiss-import-guard>"
    guard.__spec__ = importlib.machinery.ModuleSpec("faiss", loader=None)
    def unavailable(name):
        if name.startswith("__"):
            raise AttributeError(name)
        raise RuntimeError("Native FAISS required: " + name)
    guard.__getattr__ = unavailable
    sys.modules["faiss"] = guard

for p in (root, root/"core-artifact", root/"utils",
          root/"utils/dependency-utils"):
    sys.path.insert(0, str(p))

spec = importlib.util.spec_from_file_location("cta_pipeline", source)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

pipeline = module.pipeline()
pipeline.load()
pipeline.model_base.eval()

# Use the exact original inference argument mapping.
tree = ast.parse(source.read_text())
calls = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Attribute)
    and isinstance(n.func.value, ast.Name)
    and n.func.value.id == "self"
    and n.func.attr == "model_base"
]
assert len(calls) == 1

kwargs = {}
for kw in calls[0].keywords:
    assert kw.arg is not None
    v = kw.value
    assert isinstance(v, ast.Call)
    assert isinstance(v.func, ast.Attribute)
    assert isinstance(v.func.value, ast.Name)
    assert v.func.value.id == "model_in"
    assert v.func.attr == "get"
    key = ast.literal_eval(v.args[0])
    kwargs[kw.arg] = data[key]

# Capture the eight branches BEFORE the original moe_norm1.
assert hasattr(pipeline.model_base, "moe_norm1")
captured = []

def hook(module, inputs):
    assert len(inputs) == 1
    captured.append(inputs[0].detach().cpu().numpy().copy())

handle = pipeline.model_base.moe_norm1.register_forward_pre_hook(hook)

try:
    with torch.inference_mode():
        result = pipeline.model_base(**kwargs)
finally:
    handle.remove()

assert len(captured) == 1, len(captured)
branches = captured[0]
assert branches.shape == (1, 8, 256), branches.shape
assert result.shape == (1, 2048), result.shape

names = [
    "sequence", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
]
arrays = {
    name: branches[:, i, :].astype(np.float32)
    for i, name in enumerate(names)
}

out = base / "real_sanity_pytorch_branches.npz"
np.savez(out, **arrays)

print("PYTORCH EIGHT-BRANCH CAPTURE: PASS")
for name, value in arrays.items():
    print(name, value.shape, "finite:", bool(np.isfinite(value).all()))
print("SAVED:", out)
print("ORIGINAL DS AND MAX CODE UNCHANGED")
PY
