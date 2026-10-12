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
    map_location="cpu",
    weights_only=True
)
assert isinstance(data, dict) and len(data) == 17

try:
    import faiss
except ImportError:
    guard = types.ModuleType("faiss")
    guard.__file__ = "<faiss-import-only-guard>"
    guard.__spec__ = importlib.machinery.ModuleSpec(
        "faiss", loader=None
    )
    def unavailable(name):
        if name.startswith("__"):
            raise AttributeError(name)
        raise RuntimeError("Native FAISS required: " + name)
    guard.__getattr__ = unavailable
    sys.modules["faiss"] = guard

for p in (
    root, root / "core-artifact",
    root / "utils", root / "utils/dependency-utils"
):
    sys.path.insert(0, str(p))

spec = importlib.util.spec_from_file_location(
    "original_cta_pipeline", source
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

pipeline = module.pipeline()
pipeline.load()
pipeline.model_base.eval()

# Reuse the original call arguments without guessing.
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
for k in calls[0].keywords:
    assert k.arg is not None
    v = k.value
    assert isinstance(v, ast.Call)
    assert isinstance(v.func, ast.Attribute)
    assert isinstance(v.func.value, ast.Name)
    assert v.func.value.id == "model_in"
    assert v.func.attr == "get"
    key = ast.literal_eval(v.args[0])
    kwargs[k.arg] = data[key]

captured = {}

def capture(frame, event, arg):
    if event != "return" or frame.f_code.co_name != "forward":
        return

    owner = frame.f_locals.get("self")
    if owner is None or type(owner).__name__ != "GRecBase":
        return

    for name in (
        "seq_out", "ctx_out", "search_out",
        "tasks_out", "jet_out", "ihq_out", "sibling_out"
    ):
        if name in frame.f_locals:
            captured[name] = frame.f_locals[name]

sys.setprofile(capture)
try:
    with torch.inference_mode():
        result = pipeline.model_base(**kwargs)
finally:
    sys.setprofile(None)

assert result.shape == (1, 2048), result.shape

required = (
    "seq_out", "ctx_out", "search_out",
    "tasks_out", "jet_out", "ihq_out", "sibling_out"
)
assert all(k in captured for k in required), (
    "Missing original branch outputs:",
    [k for k in required if k not in captured]
)

def vector(x, label):
    assert isinstance(x, torch.Tensor), label
    a = x.detach().cpu().numpy().reshape(1, -1)
    assert a.shape == (1, 256), (label, a.shape)
    return a.astype(np.float32)

search = captured["search_out"]
assert isinstance(search, (tuple, list)) and len(search) == 2

branches = {
    "sequence": vector(captured["seq_out"], "sequence"),
    "context": vector(captured["ctx_out"], "context"),
    "search0": vector(search[0], "search0"),
    "search1": vector(search[1], "search1"),
    "task": vector(captured["tasks_out"], "task"),
    "jet": vector(captured["jet_out"], "jet"),
    "ihq": vector(captured["ihq_out"], "ihq"),
    "sibling": vector(captured["sibling_out"], "sibling")
}

out = base / "real_sanity_pytorch_branches.npz"
np.savez(out, **branches)

print("ORIGINAL PYTORCH BRANCH CAPTURE: PASS")
for name, value in branches.items():
    print(name, value.shape, "finite:", bool(np.isfinite(value).all()))

print("EIGHT ORIGINAL BRANCHES SAVED:", out)
print("ORIGINAL DS AND MAX SOURCE UNCHANGED")
PY
