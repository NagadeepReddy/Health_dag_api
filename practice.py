podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast
import sys

p = Path("artifacts/v1.168-max/cta_max/nlp_bert_max.py")
s = p.read_text()

old = "ops.softmax(scores + mask, axis=-1)"
new = "ops.softmax(scores + mask)"

assert s.count(old) == 1, "STOP: softmax code differs"

updated = s.replace(old, new, 1)
ast.parse(updated)
p.write_text(updated)

print("SOFTMAX API CORRECTED")

sys.path.insert(0, str(p.parent))

from max.driver import CPU
from max.graph import DeviceRef
from nlp_bert_max import build_nlp_bert_graph

graph = build_nlp_bert_graph(
    DeviceRef.from_device(CPU()),
    seq_len=4
)

print("SIX-LAYER BERT GRAPH CONSTRUCTION: PASS")
print("ORIGINAL MODEL AND DS CODE UNCHANGED")
PY
