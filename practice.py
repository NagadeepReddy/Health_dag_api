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
from cta_max.sibling_context_max import sibling_context_forward

data = torch.load(
    base/"real_sanity_model_in.pt",
    map_location="cpu", weights_only=True
)

# Original reference model — no preprocessing repeated.
spec = importlib.util.spec_from_file_location(
    "cta_pipeline", root/"core-artifact/pipeline.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

pipeline = module.pipeline()
pipeline.load()
pipeline.model_base.eval()

# One reusable MAX Sibling model for all ten real siblings.
device = CPU()
ref = DeviceRef.CPU()

graph = Graph(
    "cta_real_sibling_diagnostic",
    input_types=[
        TensorType(DType.int64, [1], device=ref)
        for _ in range(3)
    ] + [
        TensorType(DType.float32, [1,18], device=ref)
    ]
)

with graph:
    d0, d1, d2, wide = graph.inputs
    result = sibling_context_forward(
        [d0, d1, d2], wide, ref
    )
    graph.output(result)

model = InferenceSession(
    devices=[device]
).load(graph)

print("SIBLING ISOLATED GRAPH: PASS", flush=True)

pt_vectors = []
mx_vectors = []

for i in range(10):
    deep = data["sibling_deep_in"][:,:,i]
    wide = data["sibling_wide_in"][:,:,i]

    with torch.inference_mode():
        pt = pipeline.model_base.sibling_context_head(
            deep_in=deep.transpose(0,1),
            wide_in=wide.transpose(0,1)
        )

    pt = pt.detach().cpu().numpy()

    tensors = [
        Tensor.from_numpy(
            np.ascontiguousarray(
                deep[:,j].numpy().astype(np.int64)
            )
        ).to(device)
        for j in range(3)
    ]
    tensors.append(
        Tensor.from_numpy(
            np.ascontiguousarray(
                wide.numpy().astype(np.float32)
            )
        ).to(device)
    )

    mx = model.execute(*tensors)[0].to_numpy()

    assert pt.shape == mx.shape == (1,128), (
        i, pt.shape, mx.shape
    )

    pt_vectors.append(pt)
    mx_vectors.append(mx)

    delta = np.abs(pt.astype(np.float64)-mx.astype(np.float64))
    print(
        f"SIBLING {i}: mean={delta.mean():.7f} "
        f"max={delta.max():.7f} "
        f"match={np.allclose(pt,mx,rtol=1e-3,atol=1e-3)}"
    )

def pool(values):
    stacked = np.stack(values,axis=1)
    return np.concatenate(
        [stacked.mean(axis=1),stacked.max(axis=1)],
        axis=1
    )

pt_pool = pool(pt_vectors)
mx_pool = pool(mx_vectors)

delta = np.abs(
    pt_pool.astype(np.float64)
    - mx_pool.astype(np.float64)
)

print("\n=== ISOLATED SIBLING POOLING ===")
print("SHAPE:", mx_pool.shape)
print("MEAN DIFF:", float(delta.mean()))
print("MAX DIFF:", float(delta.max()))
print(
    "MATCH:",
    bool(np.allclose(
        pt_pool,mx_pool,rtol=1e-3,atol=1e-3
    ))
)
print("NO SOURCE FILES MODIFIED")
PY
