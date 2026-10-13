podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, types, importlib.util, importlib.machinery
from pathlib import Path
import numpy as np
import torch

root = Path("/workspace/artifacts/v1.168")
mxroot = Path("/workspace/artifacts/v1.168-max")
base = mxroot / "cta_max"

for p in (
    root, root/"core-artifact", root/"utils",
    root/"utils/dependency-utils", mxroot
):
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
from cta_max.sibling_context_max import sibling_context_forward

data = torch.load(
    base / "real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=True
)

spec = importlib.util.spec_from_file_location(
    "cta_pipeline", root / "core-artifact/pipeline.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

pipeline = module.pipeline()
pipeline.load()
head = pipeline.model_base.sibling_context_head
head.eval()

deep = data["sibling_deep_in"][:, :, 0]
wide = data["sibling_wide_in"][:, :, 0]

with torch.inference_mode():
    pt = head(
        deep_in=deep.transpose(0, 1),
        wide_in=wide.transpose(0, 1)
    ).detach().cpu().numpy()

device = CPU()
ref = DeviceRef.CPU()

graph = Graph(
    "cta_sibling_real_halves",
    input_types=[
        TensorType(DType.int64, [1], device=ref)
        for _ in range(3)
    ] + [
        TensorType(DType.float32, [1,18], device=ref)
    ]
)

with graph:
    d0, d1, d2, w = graph.inputs
    result = sibling_context_forward(
        [d0, d1, d2], w, ref
    )
    graph.output(result)

model = InferenceSession(
    devices=[device]
).load(graph)

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

mx = model.execute(*inputs)[0].to_numpy()

assert pt.shape == mx.shape == (1,128)
assert np.isfinite(pt).all() and np.isfinite(mx).all()

print("\n=== REAL SIBLING DEEP VS WIDE ===")

for label, start, end in [
    ("DEEP", 0, 64),
    ("WIDE", 64, 128),
    ("FULL", 0, 128)
]:
    a = pt[:, start:end].astype(np.float64)
    b = mx[:, start:end].astype(np.float64)
    diff = np.abs(a - b)

    print(
        f"{label}: mean={diff.mean():.8f} "
        f"max={diff.max():.8f} "
        f"match={np.allclose(a,b,rtol=1e-3,atol=1e-3)}"
    )

print("\nNO SOURCE FILES MODIFIED")
PY
