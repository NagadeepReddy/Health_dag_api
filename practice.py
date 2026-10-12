python - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_graph_sequence.py")
s = p.read_text()

old = '"cta_parallel_transformer_block_0"'
new = '"cta_parallel_transformer_sequence_combined_v1"'

assert s.count(old) == 1, "STOP: graph name differs"
assert "graph.output(postprocess(output))" in s, "STOP: postprocessing missing"

updated = s.replace(old, new, 1)
ast.parse(updated)
p.write_text(updated)

print("COMBINED GRAPH NAME UPDATED")
print("POSTPROCESS CONNECTION PRESERVED")
print("ORIGINAL TRANSFORMER AND DS CODE UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_transformer_sequence.py
