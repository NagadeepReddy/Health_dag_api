podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
import numpy as np

sys.path.insert(0, "artifacts/v1.168-max")

from max.driver import CPU
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType
from max.engine import InferenceSession
from cta_max.nlp_bert_in_graph import nlp_bert_forward

cpu = CPU()
device = DeviceRef.from_device(cpu)

graph = Graph(
    "cta_nlp_reusable_integration",
    input_types=[
        TensorType(DType.int64, [1, 4], device=device),
        TensorType(DType.int64, [1, 4], device=device),
    ],
)

with graph:
    output = nlp_bert_forward(
        graph.inputs[0],
        graph.inputs[1],
        device,
        4,
    )

    print("ADAPTER GRAPH SHAPE:", output.shape)
    graph.output(output)

print("REUSABLE NLP GRAPH: PASS", flush=True)

session = InferenceSession(devices=[cpu])
model = session.load(graph)

ids = np.array([[101, 2023, 2003, 102]], dtype=np.int64)
mask = np.array([[1, 1, 1, 1]], dtype=np.int64)

result = model.execute(ids, mask)[0].to_numpy()

assert result.shape == (1, 512), result.shape
assert np.isfinite(result).all()

print("REUSABLE NLP EXECUTION: PASS")
print("OUTPUT SHAPE:", result.shape)
print("FINITE: True")
print("NO FILES MODIFIED")
PY
