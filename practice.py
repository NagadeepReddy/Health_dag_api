podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import numpy as np
import torch
from pathlib import Path
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType, ops
from max.nn import Linear
from max.engine import InferenceSession
from max.graph.weights import WeightData

base = Path("artifacts/v1.168-max/cta_max")
wdir = base / "sequence_weights"
device = DeviceRef.CPU()

x = np.load(base / "transformer_max_output_2layers.npy").astype(np.float32)
assert x.shape == (1, 4, 256)

def load(name):
    return np.load(wdir / f"{name}.npy").astype(np.float32)

g1 = load("out_norm1_g")
g2 = load("out_norm2_g")
w = load("seq_dense_weight")
b = load("seq_dense_bias")

assert (g1.shape, g2.shape, w.shape, b.shape) == (
    (256,), (256,), (256, 512), (256,)
)

dense = Linear(
    in_dim=512,
    out_dim=256,
    dtype=DType.float32,
    device=device,
    has_bias=True,
    name="sequence_transformer.seq_dense"
)

graph = Graph(
    "cta_sequence_postprocess_test",
    input_types=[
        TensorType(DType.float32, shape=[1, 4, 256], device=device)
    ]
)

with graph:
    v = graph.inputs[0]

    norm1 = ops.constant(g1, dtype=DType.float32, device=device)
    norm2 = ops.constant(g2, dtype=DType.float32, device=device)

    var1 = ops.reshape(ops.mean(v * v, axis=-1), [1, 4, 1])
    v = v * ops.rsqrt(var1 + 1e-6) * norm1

    mean = ops.mean(v, axis=1)
    maximum = ops.max(v, axis=1)

    v = ops.reshape(
        ops.concat([mean, maximum], axis=1),
        [1, 512]
    )

    v = dense(v)

    var2 = ops.reshape(ops.mean(v * v, axis=-1), [1, 1])
    v = v * ops.rsqrt(var2 + 1e-6) * norm2

    graph.output(v)

registry = {}

for name, arr in {
    "sequence_transformer.seq_dense.weight": w,
    "sequence_transformer.seq_dense.bias": b
}.items():
    registry[name] = WeightData(
        arr,
        name=name,
        dtype=DType.float32,
        shape=arr.shape
    )

session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=registry)
max_out = model.execute(x)[0].to_numpy()

with torch.no_grad():
    t = torch.from_numpy(x)
    t = t * torch.rsqrt(t.square().mean(-1, keepdim=True) + 1e-6) * torch.from_numpy(g1)
    t = torch.cat([t.mean(1), t.max(1).values], dim=1)
    t = torch.nn.functional.linear(t, torch.from_numpy(w), torch.from_numpy(b))
    t = t * torch.rsqrt(t.square().mean(-1, keepdim=True) + 1e-6) * torch.from_numpy(g2)
    pt_out = t.numpy()

print("PT SHAPE :", pt_out.shape)
print("MAX SHAPE:", max_out.shape)
print("MAX DIFF :", np.max(np.abs(pt_out - max_out)))
print("MATCH    :", np.allclose(pt_out, max_out, rtol=1e-4, atol=1e-5))
PY
