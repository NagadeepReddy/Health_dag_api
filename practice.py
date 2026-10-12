podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast
import sys
import numpy as np

from max.driver import CPU
from max.dtype import DType
from max.graph import DeviceRef
from max.graph.weights import WeightData
from max.engine import InferenceSession

base = Path("artifacts/v1.168-max/cta_max")
dst = base / "grecbase_fusion_graph_max.py"
wdir = base / "grecbase_integration_weights"

assert not dst.exists(), "STOP: fusion graph already exists"

for name in (
    "att_pooling.fused_attn_ff_proj.weight",
    "att_pooling.attn_out.weight",
    "att_pooling.ff_out.1.weight",
    "att_pooling.rotary_emb.inv_freq",
    "moe_norm1.g",
    "moe_norm2.g",
):
    assert (wdir / (name + ".npy")).is_file(), \
        f"STOP: missing {name}"

assert (base / "att_pooling_max.py").is_file()
assert (base / "grecbase_get_path_max.py").is_file()

code = '''
from pathlib import Path
import numpy as np

from max.dtype import DType
from max.graph import Graph, TensorType, ops

from cta_max.att_pooling_max import AttPoolingBlockMAX
from cta_max.grecbase_get_path_max import grecbase_get_path_max

WDIR = Path(__file__).parent / "grecbase_integration_weights"

def build_grecbase_fusion_graph(device):
    block = AttPoolingBlockMAX(
        dtype=DType.float32,
        device=device,
        layer_idx=0,
    )

    graph = Graph(
        "cta_grecbase_eight_branch_fusion",
        input_types=[
            TensorType(DType.float32, [1, 256], device=device)
            for _ in range(8)
        ],
    )

    with graph:
        # Exact original order:
        # sequence, context, search0, search1,
        # task, jet, IHQ, sibling
        outs = ops.concat(
            [
                ops.reshape(x, [1, 1, 256])
                for x in graph.inputs
            ],
            axis=1,
        )

        def norm(x, name):
            arr = np.load(
                WDIR / (name + ".g.npy")
            ).astype(np.float32)
            assert arr.shape == (256,)

            g = ops.constant(
                arr, dtype=DType.float32, device=device
            )
            variance = ops.reshape(
                ops.mean(x * x, axis=-1),
                [1, 8, 1],
            )
            return x * ops.rsqrt(
                variance + 1e-6
            ) * g

        outs = norm(outs, "moe_norm1")

        inv = np.load(
            WDIR / "att_pooling.rotary_emb.inv_freq.npy"
        ).astype(np.float32)
        assert inv.shape == (128,)

        angles = (
            np.arange(8, dtype=np.float32)[:, None]
            * inv[None, :]
        )

        position = np.concatenate(
            [angles, angles], axis=-1
        )[None, None, :, :].astype(np.float32)

        pos = ops.constant(
            position, dtype=DType.float32, device=device
        )

        outs = block(outs, pos)
        outs = norm(outs, "moe_norm2")
        outs = ops.reshape(outs, [1, 2048])

        # Existing validated task-0 get_path implementation.
        result = grecbase_get_path_max(outs, device)

        graph.output(result)

    return graph
'''

ast.parse(code)

sys.path.insert(0, str(base.parent))

namespace = {
    "__name__": "cta_max.grecbase_fusion_preflight",
    "__package__": "cta_max",
    "__file__": str(dst),
}

exec(compile(code, str(dst), "exec"), namespace)

cpu = CPU()
device = DeviceRef.from_device(cpu)

graph = namespace["build_grecbase_fusion_graph"](device)

print("FUSION GRAPH CONSTRUCTION: PASS", flush=True)

registry = {}

expected = {
    "att_pooling.fused_attn_ff_proj.weight": (2816, 256),
    "att_pooling.attn_out.weight": (256, 256),
    "att_pooling.ff_out.1.weight": (256, 1024),
}

for name, shape in expected.items():
    arr = np.load(wdir / (name + ".npy")).astype(np.float32)
    assert arr.shape == shape

    registry[name] = WeightData(
        arr,
        name=name,
        dtype=DType.float32,
        shape=arr.shape,
    )

session = InferenceSession(devices=[cpu])
model = session.load(graph, weights_registry=registry)

print("FUSION COMPILATION: PASS", flush=True)

rng = np.random.default_rng(42)
inputs = [
    rng.standard_normal((1, 256)).astype(np.float32) * 0.01
    for _ in range(8)
]

out = model.execute(*inputs)[0].to_numpy()

print("OUTPUT SHAPE:", out.shape)
print("FINITE:", bool(np.isfinite(out).all()))

assert out.shape == (1, 2048)
assert np.isfinite(out).all()

dst.write_text(code)

print("GRECBASE FUSION GRAPH SAVED")
print("EIGHT BRANCHES + ATTENTION + GET_PATH CONNECTED")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
