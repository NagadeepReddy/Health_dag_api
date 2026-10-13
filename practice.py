cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import numpy as np

sys.path.insert(0, "/workspace/artifacts/v1.168-max")

from max.driver import CPU, Tensor
from max.dtype import DType
from max.graph import Graph, TensorType, DeviceRef
from max.engine import InferenceSession
from cta_max.grecbase_get_path_max import grecbase_get_path_max

base = "/workspace/artifacts/v1.168-max/cta_max"
fusion = np.load(
    base + "/real_sanity_max_2048_verified_latest.npy"
).astype(np.float32)

device = DeviceRef.CPU()

graph = Graph(
    "cta_isolated_trained_head",
    input_types=[
        TensorType(DType.float32, [1, 2048], device=device)
    ],
)

with graph:
    output = grecbase_get_path_max(graph.inputs[0], device)
    graph.output(output)

session = InferenceSession(devices=[CPU()])
model = session.load(graph)

result = model.execute(Tensor.from_numpy(fusion).to(CPU()))[0]
head = result.to_numpy()

print("HEAD OUTPUT SHAPE:", head.shape)
print("HEAD FINITE:", bool(np.isfinite(head).all()))
print("ISOLATED HEAD VS FUSION:",
      float(np.max(np.abs(head - fusion))))
print("ISOLATED HEAD EXECUTION: PASS")
PY
