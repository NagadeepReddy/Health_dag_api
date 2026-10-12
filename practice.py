podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
import numpy as np

sys.path.insert(0, "artifacts/v1.168-max/cta_max")

from max.driver import CPU
from max.graph import DeviceRef
from max.engine import InferenceSession
from nlp_bert_max import build_nlp_bert_graph

cpu = CPU()
device = DeviceRef.from_device(cpu)

graph = build_nlp_bert_graph(device, seq_len=4)
print("BERT GRAPH: PASS", flush=True)

session = InferenceSession(devices=[cpu])

print("COMPILING BERT...", flush=True)
model = session.load(graph)
print("BERT COMPILATION: PASS", flush=True)

input_ids = np.array(
    [[101, 2023, 2003, 102]],
    dtype=np.int64
)

attention_mask = np.array(
    [[1, 1, 1, 1]],
    dtype=np.int64
)

print("RUNNING BERT INFERENCE...", flush=True)

result = model.execute(input_ids, attention_mask)
output = result[0].to_numpy()

print("BERT OUTPUT SHAPE:", output.shape)
print("FINITE:", bool(np.isfinite(output).all()))
print("BERT EXECUTION PASS:",
      output.shape == (1, 256)
      and bool(np.isfinite(output).all()))
PY
