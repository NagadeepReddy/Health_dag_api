python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
src = base / "parallel_transformer_graph.py"
dst = base / "parallel_transformer_graph_layer1.py"

s = src.read_text()

old_import = "from parallel_transformer_block import ParallelTransformerBlockMAX"
old_call = """block = ParallelTransformerBlockMAX(
        dtype=DType.float32,
        device=device_ref,
    )"""
new_call = """block = ParallelTransformerBlockMAX(
        dtype=DType.float32,
        device=device_ref,
        layer_idx=1,
    )"""

assert s.count(old_import) == 1, "STOP: import differs"
assert s.count(old_call) == 1, "STOP: constructor differs"
assert not dst.exists(), "STOP: graph already exists"

s = s.replace(
    old_import,
    "from parallel_transformer_block_multilayer import ParallelTransformerBlockMAX",
    1
)
s = s.replace(old_call, new_call, 1)

ast.parse(s)
dst.write_text(s)

print("BLOCK-1 GRAPH CREATED — SYNTAX OK")
print("VERIFIED BLOCK-0 UNCHANGED")
PY
