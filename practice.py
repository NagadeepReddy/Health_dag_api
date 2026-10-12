podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast, sys
import numpy as np
import torch
import torch.nn.functional as F

from max.driver import CPU
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType
from max.engine import InferenceSession

base = Path("artifacts/v1.168-max/cta_max")
dst = base / "sibling_context_max.py"
wdir = base / "sibling_context_weights"

assert not dst.exists(), "STOP: sibling module already exists"
assert len(list(wdir.glob("*.npy"))) == 20

code = '''
from pathlib import Path
import numpy as np
from max.dtype import DType
from max.graph import ops

WDIR = Path(__file__).parent / "sibling_context_weights"

def sibling_context_forward(deep_ids, wide_input, device):
    def weight(name):
        arr = np.load(WDIR / (name + ".npy")).astype(np.float32)
        return ops.constant(arr, dtype=DType.float32, device=device)

    def linear(x, prefix, bias=True):
        y = ops.matmul(
            x, ops.permute(weight(prefix + ".weight"), [1, 0])
        )
        if bias:
            y = y + weight(prefix + ".bias")
        return y

    def rms(x, name):
        return x * ops.rsqrt(
            ops.mean(x * x, axis=-1) + 1e-6
        ) * weight(name + ".g")

    def swiglu(x, name):
        a = linear(x, name + ".w1", False)
        b = linear(x, name + ".w3", False)
        return linear(a * ops.sigmoid(a) * b, name + ".w2", False)

    p = "sibling_context_head"

    embeddings = [
        ops.reshape(
            ops.gather(
                weight(f"{p}.deep_embedding.{i}.weight"),
                deep_ids[i], axis=0
            ),
            [1, 128]
        )
        for i in range(3)
    ]

    deep = ops.concat(embeddings, axis=1)
    deep = ops.relu(deep) - 0.2 * ops.relu(-deep)
    deep = rms(deep, p + ".deep_norm")
    deep = swiglu(
        linear(deep, p + ".deep_dense"),
        p + ".deep_swiglu"
    )

    wide = (
        wide_input - weight(p + ".num_batch_norm.running_mean")
    ) / ops.sqrt(
        weight(p + ".num_batch_norm.running_var") + 1e-5
    )

    wide = (
        wide * weight(p + ".num_batch_norm.weight")
        + weight(p + ".num_batch_norm.bias")
    )

    wide = rms(wide, p + ".wide_norm")
    wide = linear(wide, p + ".wide_dense")
    wide = ops.relu(wide) - 0.2 * ops.relu(-wide)
    wide = swiglu(wide, p + ".wide_swiglu")

    return ops.concat([deep, wide], axis=1)
'''

ast.parse(code)
dst.write_text(code)

sys.path.insert(0, str(base))
from sibling_context_max import sibling_context_forward

cpu = CPU()
device = DeviceRef.from_device(cpu)

graph = Graph(
    "cta_sibling_context",
    input_types=[
        *[
            TensorType(DType.int64, [1, 1], device=device)
            for _ in range(3)
        ],
        TensorType(DType.float32, [1, 18], device=device),
    ],
)

with graph:
    output = sibling_context_forward(
        list(graph.inputs[:3]),
        graph.inputs[3],
        device
    )
    graph.output(output)

print("SIBLING GRAPH CONSTRUCTION: PASS", flush=True)

session = InferenceSession(devices=[cpu])
model = session.load(graph)

inputs = [
    np.array([[1]], dtype=np.int64),
    np.array([[2]], dtype=np.int64),
    np.array([[3]], dtype=np.int64),
    np.arange(18, dtype=np.float32).reshape(1, 18) / 10,
]

result = model.execute(*inputs)[0].to_numpy()

print("SIBLING OUTPUT SHAPE:", result.shape)
print("FINITE:", bool(np.isfinite(result).all()))
print("SIBLING EXECUTION PASS:",
      result.shape == (1, 128) and np.isfinite(result).all())
print("ORIGINAL MODEL AND DS CODE UNCHANGED")
PY
