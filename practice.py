podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

from max.driver import CPU
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType
from max.engine import InferenceSession

base = Path("artifacts/v1.168-max/cta_max")
sys.path.insert(0, str(base))
from sibling_context_max import sibling_context_forward

wdir = base / "sibling_context_weights"
prefix = "sibling_context_head"

def w(name):
    return torch.from_numpy(
        np.load(wdir / (name + ".npy")).astype(np.float32)
    )

def linear(x, name, bias=True):
    return F.linear(
        x, w(name + ".weight"),
        w(name + ".bias") if bias else None
    )

def rms(x, name):
    return (
        x * torch.rsqrt(
            x.square().mean(dim=-1, keepdim=True) + 1e-6
        ) * w(name + ".g")
    )

def swiglu(x, name):
    a = linear(x, name + ".w1", False)
    b = linear(x, name + ".w3", False)
    return linear(F.silu(a) * b, name + ".w2", False)

inputs = [
    np.array([[1]], dtype=np.int64),
    np.array([[2]], dtype=np.int64),
    np.array([[3]], dtype=np.int64),
    np.arange(18, dtype=np.float32).reshape(1, 18) / 10,
]

with torch.inference_mode():
    deep = torch.cat([
        F.embedding(
            torch.from_numpy(inputs[i]),
            w(f"{prefix}.deep_embedding.{i}.weight")
        ).reshape(1, 128)
        for i in range(3)
    ], dim=1)

    deep = F.leaky_relu(deep, negative_slope=0.2)
    deep = rms(deep, prefix + ".deep_norm")
    deep = swiglu(
        linear(deep, prefix + ".deep_dense"),
        prefix + ".deep_swiglu"
    )

    wide = F.batch_norm(
        torch.from_numpy(inputs[3]),
        w(prefix + ".num_batch_norm.running_mean"),
        w(prefix + ".num_batch_norm.running_var"),
        w(prefix + ".num_batch_norm.weight"),
        w(prefix + ".num_batch_norm.bias"),
        training=False,
        eps=1e-5
    )

    wide = rms(wide, prefix + ".wide_norm")
    wide = F.leaky_relu(
        linear(wide, prefix + ".wide_dense"),
        negative_slope=0.2
    )
    wide = swiglu(wide, prefix + ".wide_swiglu")

    pt_out = torch.cat([deep, wide], dim=1).numpy()

cpu = CPU()
device = DeviceRef.from_device(cpu)

graph = Graph(
    "cta_sibling_parity",
    input_types=[
        TensorType(DType.int64, [1, 1], device=device),
        TensorType(DType.int64, [1, 1], device=device),
        TensorType(DType.int64, [1, 1], device=device),
        TensorType(DType.float32, [1, 18], device=device)
    ]
)

with graph:
    output = sibling_context_forward(
        list(graph.inputs[:3]),
        graph.inputs[3],
        device
    )
    graph.output(output)

session = InferenceSession(devices=[cpu])
model = session.load(graph)
max_out = model.execute(*inputs)[0].to_numpy()

print("PYTORCH SHAPE:", pt_out.shape)
print("MAX SHAPE:", max_out.shape)
print("MAX DIFF:", np.max(np.abs(pt_out - max_out)))
print("MATCH:", np.allclose(
    pt_out, max_out, rtol=1e-4, atol=1e-5
))
print("BOTH FINITE:", bool(
    np.isfinite(pt_out).all() and np.isfinite(max_out).all()
))
PY
