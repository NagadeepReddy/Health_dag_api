python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
src = base / "parallel_transformer_graph.py"
dst = base / "parallel_transformer_graph_layer1.py"

s = src.read_text()

old = "from parallel_transformer_block import ParallelTransformerBlockMAX"
assert s.count(old) == 1, "STOP: import differs"
assert not dst.exists(), "STOP: graph already exists"

s = s.replace(
    old,
    "from parallel_transformer_block_multilayer import ParallelTransformerBlockMAX",
    1
)

old_call = "device=device_ref,"
assert s.count(old_call) == 1, "STOP: constructor differs"

s = s.replace(
    old_call,
    old_call + "\n        layer_idx=1,",
    1
)

ast.parse(s)
dst.write_text(s)

print("BLOCK-1 GRAPH READY — SYNTAX OK")
print("BLOCK-0 UNCHANGED")
PY
