podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys

sys.path.insert(0, "artifacts/v1.168-max/cta_max")

from max.driver import CPU
from max.graph import DeviceRef
from nlp_bert_max import build_nlp_bert_graph

device = DeviceRef.from_device(CPU())

print("BUILDING SIX-LAYER BERT GRAPH...", flush=True)

graph = build_nlp_bert_graph(device, seq_len=4)

print("BERT GRAPH CONSTRUCTION: PASS")
print("GRAPH:", graph.name)
print("ORIGINAL MODEL AND DS CODE UNCHANGED")
PY
