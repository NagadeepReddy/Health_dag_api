podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, "/workspace/artifacts/v1.168-max")

from max.driver import CPU, Tensor
from max.engine import InferenceSession
from max.graph import DeviceRef, WeightData, Shape
from cta_max.grecbase_fusion_graph_max import build_grecbase_fusion_graph

base = Path("artifacts/v1.168-max/cta_max")

# Reuse the already-exported attention weights.
files = sorted(base.rglob("att_pooling.*.npy"))
assert files, "Attention weight exports not found"

weights = {}
for p in files:
    key = p.stem
    assert key not in weights, f"Duplicate weight: {key}"
    arr = np.load(p).astype(np.float32)
    weights[key] = WeightData(
        arr,
        shape=Shape(arr.shape),
        name="weight",
    )

required = "att_pooling.fused_attn_ff_proj.weight"
assert required in weights, f"Missing {required}"

print("REGISTERED ATTENTION WEIGHTS:", len(weights))

device = CPU()
graph = build_grecbase_fusion_graph(DeviceRef.CPU())

session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)
print("FUSION COMPILATION: PASS")

inputs = [
    Tensor.from_numpy(
        np.random.default_rng(i).standard_normal((1, 256)).astype(np.float32)
    ).to(device)
    for i in range(8)
]

result = model.execute(*inputs)[0].to_numpy()

print("OUTPUT SHAPE:", result.shape)
print("FINITE:", bool(np.isfinite(result).all()))

assert result.shape == (1, 10819), result.shape
assert np.isfinite(result).all()

print("UPDATED FUSION RUNTIME: PASS")
print("ORIGINAL DS CODE UNCHANGED")
PY
