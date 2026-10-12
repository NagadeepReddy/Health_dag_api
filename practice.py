podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
import numpy as np
from pathlib import Path

from max.driver import CPU
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType
from max.graph.weights import WeightData
from max.engine import InferenceSession

base = Path("artifacts/v1.168-max/cta_max")
wdir = base / "grecbase_integration_weights"

sys.path.insert(0, str(base))
from att_pooling_max import AttPoolingBlockMAX

cpu = CPU()
device = DeviceRef.from_device(cpu)

block = AttPoolingBlockMAX(
    dtype=DType.float32,
    device=device,
    layer_idx=0,
)

assert block.heads == 1
assert tuple(block.fused_dims) == (256, 256, 256, 2048)

def load(name):
    p = wdir / (name + ".npy")
    assert p.is_file(), f"STOP: missing {p}"
    return np.load(p).astype(np.float32)

mapping = {
    "att_pooling.fused_attn_ff_proj.weight":
        (2816, 256),
    "att_pooling.attn_out.weight":
        (256, 256),
    "att_pooling.ff_out.1.weight":
        (256, 1024),
}

registry = {}

for name, shape in mapping.items():
    arr = load(name)
    assert arr.shape == shape, (
        f"STOP: {name}: {arr.shape}"
    )
    registry[name] = WeightData(
        arr,
        name=name,
        dtype=DType.float32,
        shape=arr.shape,
    )

inv_freq = load("att_pooling.rotary_emb.inv_freq")
assert inv_freq.shape == (128,)

positions = np.arange(8, dtype=np.float32)
angles = positions[:, None] * inv_freq[None, :]

pos = np.concatenate(
    [angles, angles], axis=-1
)[None, None, :, :].astype(np.float32)

x = (
    np.random.default_rng(42)
    .standard_normal((1, 8, 256))
    .astype(np.float32) * 0.01
)

graph = Graph(
    "cta_grecbase_attention_one_head_test",
    input_types=[
        TensorType(
            DType.float32, [1, 8, 256], device=device
        ),
        TensorType(
            DType.float32, [1, 1, 8, 256], device=device
        ),
    ],
)

with graph:
    y = block(*graph.inputs)
    print("DECLARED OUTPUT SHAPE:", y.shape)
    graph.output(y)

print("ATTENTION GRAPH: PASS", flush=True)

session = InferenceSession(devices=[cpu])
model = session.load(
    graph,
    weights_registry=registry,
)

print("ATTENTION COMPILATION: PASS", flush=True)

result = model.execute(x, pos)[0].to_numpy()

print("ATTENTION OUTPUT SHAPE:", result.shape)
print("FINITE:", bool(np.isfinite(result).all()))
print(
    "ATTENTION EXECUTION PASS:",
    result.shape == (1, 8, 256)
    and bool(np.isfinite(result).all())
)
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
