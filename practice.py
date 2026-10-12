podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
from pathlib import Path
import numpy as np

from max.driver import CPU
from max.dtype import DType
from max.engine import InferenceSession
from max.graph import DeviceRef, Graph, TensorType
from max.graph.weights import WeightData

base = Path("artifacts/v1.168-max/cta_max")
sys.path.insert(0, str(base))

from att_pooling_max import AttPoolingBlockMAX

wdir = base / "grecbase_integration_weights"

cpu = CPU()
device = DeviceRef.from_device(cpu)

block = AttPoolingBlockMAX(
    dtype=DType.float32,
    device=device,
    layer_idx=0
)

assert block.heads == 1
assert tuple(block.fused_dims) == (256, 256, 256, 2048)

expected = {
    "att_pooling.fused_attn_ff_proj.weight": (2816, 256),
    "att_pooling.attn_out.weight": (256, 256),
    "att_pooling.ff_out.1.weight": (256, 1024),
}

registry = {}

for name, shape in expected.items():
    path = wdir / (name + ".npy")
    assert path.is_file(), f"STOP: missing {name}"

    arr = np.load(path).astype(np.float32)
    assert arr.shape == shape, f"STOP: wrong shape {name}"

    registry[name] = WeightData(
        arr,
        name=name,
        dtype=DType.float32,
        shape=arr.shape
    )

inv = np.load(
    wdir / "att_pooling.rotary_emb.inv_freq.npy"
).astype(np.float32)

assert inv.shape == (128,)

angles = np.arange(8, dtype=np.float32)[:, None] * inv[None, :]
pos = np.concatenate([angles, angles], axis=-1)
pos = pos[None, None, :, :].astype(np.float32)

x = (
    np.random.default_rng(42)
    .standard_normal((1, 8, 256))
    .astype(np.float32) * 0.01
)

graph = Graph(
    "cta_attention_execution_verified",
    input_types=[
        TensorType(DType.float32, [1, 8, 256], device=device),
        TensorType(DType.float32, [1, 1, 8, 256], device=device),
    ],
)

with graph:
    output = block(*graph.inputs)
    graph.output(output)

print("GRAPH CONSTRUCTION: PASS", flush=True)

session = InferenceSession(devices=[cpu])
model = session.load(graph, weights_registry=registry)

print("ATTENTION COMPILATION: PASS", flush=True)

result = model.execute(x, pos)[0].to_numpy()

print("OUTPUT SHAPE:", result.shape)
print("FINITE:", bool(np.isfinite(result).all()))
print(
    "ATTENTION EXECUTION PASS:",
    result.shape == (1, 8, 256)
    and bool(np.isfinite(result).all())
)
print("NO FILES MODIFIED")
PY
