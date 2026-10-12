podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, ast, types, importlib.util, importlib.machinery
from pathlib import Path
import numpy as np
import torch

root = Path("/workspace/artifacts/v1.168")
base = Path("/workspace/artifacts/v1.168-max/cta_max")

saved = base / "real_sanity_model_in.pt"
max_file = base / "real_sanity_max_output.npy"
assert saved.is_file() and max_file.is_file()

model_in = torch.load(
    saved, map_location="cpu", weights_only=True
)
max_out = np.load(max_file)
assert isinstance(model_in, dict) and len(model_in) == 17

# Import-only FAISS guard, as used in successful preprocessing.
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
    root,
    root / "core-artifact",
    root / "utils",
    root / "utils/dependency-utils",
):
    sys.path.insert(0, str(p))

pipeline_file = root / "core-artifact/pipeline.py"
spec = importlib.util.spec_from_file_location(
    "original_cta_pipeline", pipeline_file
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

pipeline = module.pipeline()
pipeline.load()
print("ORIGINAL PYTORCH MODEL LOADED: PASS", flush=True)

# Extract the exact model argument mapping from the
# original inference method instead of guessing.
tree = ast.parse(pipeline_file.read_text())
calls = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Attribute)
    and isinstance(n.func.value, ast.Name)
    and n.func.value.id == "self"
    and n.func.attr == "model_base"
]
assert len(calls) == 1, (
    f"Expected one original model_base call, found {len(calls)}"
)

call = calls[0]
assert not call.args, "Unexpected positional model arguments"

kwargs = {}
for kw in call.keywords:
    assert kw.arg is not None
    value = kw.value
    assert (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and isinstance(value.func.value, ast.Name)
        and value.func.value.id == "model_in"
        and value.func.attr == "get"
        and len(value.args) == 1
    ), f"Unexpected original argument: {kw.arg}"

    key = ast.literal_eval(value.args[0])
    assert key in model_in, f"Missing original input: {key}"
    kwargs[kw.arg] = model_in[key]

print("ORIGINAL MODEL ARGUMENTS:", len(kwargs), flush=True)

pipeline.model_base.eval()
with torch.inference_mode():
    reference = pipeline.model_base(**kwargs)

assert isinstance(reference, torch.Tensor), (
    f"Unexpected PyTorch output: {type(reference)}"
)

pt_out = reference.detach().cpu().numpy()
np.save(base / "real_sanity_pytorch_output.npy", pt_out)

print("PYTORCH OUTPUT SHAPE:", pt_out.shape)
print("MAX OUTPUT SHAPE:", max_out.shape)
print("PYTORCH FINITE:", bool(np.isfinite(pt_out).all()))
print("MAX FINITE:", bool(np.isfinite(max_out).all()))

assert pt_out.shape == max_out.shape, (
    "Output-shape mismatch", pt_out.shape, max_out.shape
)

difference = np.abs(
    pt_out.astype(np.float64) - max_out.astype(np.float64)
)

print("MEAN ABS DIFFERENCE:", float(difference.mean()))
print("MAX ABS DIFFERENCE:", float(difference.max()))
print("ALLCLOSE (1e-3):", bool(np.allclose(
    pt_out, max_out, rtol=1e-3, atol=1e-3
)))

pt_top = np.argsort(pt_out.reshape(-1))[-10:][::-1]
max_top = np.argsort(max_out.reshape(-1))[-10:][::-1]

print("PYTORCH TOP-10 INDICES:", pt_top.tolist())
print("MAX TOP-10 INDICES:", max_top.tolist())
print("TOP-10 OVERLAP:", len(set(pt_top) & set(max_top)), "/ 10")

print("PYTORCH REFERENCE OUTPUT SAVED")
print("ORIGINAL DS AND PYTORCH SOURCE UNCHANGED")
PY
