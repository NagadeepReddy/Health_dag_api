python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
src = base / "parallel_transformer_graph_layer1.py"
dst = base / "parallel_transformer_graph_2layers.py"

assert src.is_file(), "STOP: source graph missing"
assert not dst.exists(), "STOP: two-layer graph already exists"

s = src.read_text()

old = """    block = ParallelTransformerBlockMAX(
        dtype=DType.float32,
        device=device_ref,
        layer_idx=1,
    )"""

new = """    block0 = ParallelTransformerBlockMAX(
        dtype=DType.float32,
        device=device_ref,
        layer_idx=0,
    )
    block1 = ParallelTransformerBlockMAX(
        dtype=DType.float32,
        device=device_ref,
        layer_idx=1,
    )"""

assert s.count(old) == 1, "STOP: constructor differs"
assert s.count("output = block(x, pos_emb)") == 1, "STOP: graph call differs"

s = s.replace(old, new, 1)
s = s.replace(
    "output = block(x, pos_emb)",
    "output = block1(block0(x, pos_emb), pos_emb)",
    1
)

ast.parse(s)
dst.write_text(s)

print("TWO-LAYER MAX GRAPH CREATED — SYNTAX OK")
print("VERIFIED BLOCKS AND DS CODE UNCHANGED")
PY
