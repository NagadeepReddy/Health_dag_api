podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast, sys, types, importlib.util, importlib.machinery
from pathlib import Path
import numpy as np
import torch

root = Path("/workspace/artifacts/v1.168")
mxroot = Path("/workspace/artifacts/v1.168-max")
base = mxroot / "cta_max"

for p in (root, root/"core-artifact", root/"utils",
          root/"utils/dependency-utils", mxroot):
    sys.path.insert(0, str(p))

try:
    import faiss
except ImportError:
    guard = types.ModuleType("faiss")
    guard.__file__ = "<import-only-guard>"
    guard.__spec__ = importlib.machinery.ModuleSpec("faiss", None)
    def missing(name):
        if name.startswith("__"):
            raise AttributeError(name)
        raise RuntimeError("Native FAISS required: " + name)
    guard.__getattr__ = missing
    sys.modules["faiss"] = guard

from max.driver import CPU, Tensor
from max.engine import InferenceSession
from max.graph import Graph, TensorType, DeviceRef
from max.dtype import DType

data = torch.load(
    base/"real_sanity_model_in.pt",
    map_location="cpu", weights_only=True
)

# Original loaded PyTorch model.
spec = importlib.util.spec_from_file_location(
    "cta_pipeline", root/"core-artifact/pipeline.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

pipeline = module.pipeline()
pipeline.load()
head = pipeline.model_base.sibling_context_head
head.eval()

captured = {}
hooks = []

for name, layer in head.named_modules():
    if name in ("deep_swiglu", "wide_swiglu",
                "num_batch_norm", "wide_dense"):
        def capture(m, args, output, label=name):
            captured[label] = output.detach().cpu().numpy()
        hooks.append(layer.register_forward_hook(capture))

deep = data["sibling_deep_in"][:, :, 0]
wide = data["sibling_wide_in"][:, :, 0]

try:
    with torch.inference_mode():
        pt = head(
            deep_in=deep.transpose(0, 1),
            wide_in=wide.transpose(0, 1)
        ).detach().cpu().numpy()
finally:
    for h in hooks:
        h.remove()

# Instrument the EXISTING MAX function in memory only.
source = base/"sibling_context_max.py"
tree = ast.parse(source.read_text())
fns = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "sibling_context_forward"
]
assert len(fns) == 1, "Sibling function not found"

fn = fns[0]
returns = [
    n for n in ast.walk(fn)
    if isinstance(n, ast.Return)
]
assert len(returns) == 1

original_return = returns[0].value
returns[0].value = ast.Tuple(
    elts=[
        original_return,
        ast.Name(id="deep", ctx=ast.Load()),
        ast.Name(id="wide", ctx=ast.Load())
    ],
    ctx=ast.Load()
)

ns = {
    "__file__": str(source),
    "__name__": "cta_max.sibling_stage_check",
    "__package__": "cta_max"
}
exec(
    compile(ast.fix_missing_locations(tree), str(source), "exec"),
    ns
)

device = CPU()
ref = DeviceRef.CPU()

graph = Graph(
    "cta_sibling_stage_check",
    input_types=[
        TensorType(DType.int64, [1], device=ref)
        for _ in range(3)
    ] + [
        TensorType(DType.float32, [1, 18], device=ref)
    ]
)

with graph:
    d0, d1, d2, w = graph.inputs
    full, deep_part, wide_part = ns[
        "sibling_context_forward"
    ]([d0, d1, d2], w, ref)
    graph.output(full, deep_part, wide_part)

session = InferenceSession(devices=[device])
model = session.load(graph)

inputs = [
    Tensor.from_numpy(
        np.ascontiguousarray(
            deep[:, j].numpy().astype(np.int64)
        )
    ).to(device)
    for j in range(3)
]
inputs.append(
    Tensor.from_numpy(
        np.ascontiguousarray(
            wide.numpy().astype(np.float32)
        )
    ).to(device)
)

results = [
    x.to_numpy() for x in model.execute(*inputs)
]
mx, mx_deep, mx_wide = results

def compare(name, a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    print(name, "SHAPES:", a.shape, b.shape)
    if a.shape == b.shape:
        diff = np.abs(a.astype(np.float64)-b.astype(np.float64))
        print(
            "  MEAN:", float(diff.mean()),
            "MAX:", float(diff.max()),
            "MATCH:", bool(np.allclose(
                a, b, rtol=1e-3, atol=1e-3
            ))
        )

print("\n=== REAL SIBLING STAGE COMPARISON ===")
compare("FULL", pt, mx)

if "deep_swiglu" in captured:
    compare("DEEP", captured["deep_swiglu"], mx_deep)
else:
    print("DEEP HOOK: unavailable")

if "wide_swiglu" in captured:
    compare("WIDE", captured["wide_swiglu"], mx_wide)
else:
    print("WIDE HOOK: unavailable")

print("PYTORCH STAGES CAPTURED:", sorted(captured))
print("NO FILES MODIFIED")
PY
