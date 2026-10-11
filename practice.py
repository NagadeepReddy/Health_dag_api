python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
src = base / "run_transformer_max.py"
dst = base / "run_transformer_layer1.py"

s = src.read_text()

changes = {
    "from parallel_transformer_graph import": "from parallel_transformer_graph_layer1 import",
    "fn_norm1_g.npy": "fn_norm1_g_layer1.npy",
    "fn_norm2_g.npy": "fn_norm2_g_layer1.npy",
    "fn_fused_attn_ff_proj_weight.npy": "fn_fused_attn_ff_proj_weight_layer1.npy",
    "fn_attn_out_weight.npy": "fn_attn_out_weight_layer1.npy",
    "fn_ff_out_1_weight.npy": "fn_ff_out_1_weight_layer1.npy",
}

assert src.is_file(), "STOP: original runner missing"
assert not dst.exists(), "STOP: Block-1 runner already exists"

for old, new in changes.items():
    assert s.count(old) == 1, f"STOP: expected one {old}, found {s.count(old)}"
    s = s.replace(old, new, 1)

ast.parse(s)

for filename in list(changes.values())[1:]:
    assert (base / "sequence_weights" / filename).is_file(), \
        f"STOP: missing {filename}"

dst.write_text(s)

print("BLOCK-1 RUNNER CREATED — SYNTAX OK")
print("BLOCK-1 WEIGHTS VERIFIED")
print("BLOCK-0 AND DS CODE UNCHANGED")
PY
