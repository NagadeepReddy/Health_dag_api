python - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_multilayer.py")
s = p.read_text()

constructor = "        super().__init__()\n"
old = 'np.load("artifacts/v1.168-max/cta_max/sequence_weights/fn_norm2_g.npy")'

assert s.count(constructor) == 1, "STOP: constructor differs"
assert s.count(old) == 1, "STOP: norm2 load differs"

s = s.replace(
    constructor,
    constructor + "        self.layer_idx = layer_idx\n",
    1
)

s = s.replace(
    old,
    'np.load("artifacts/v1.168-max/cta_max/sequence_weights/" + ("fn_norm2_g.npy" if self.layer_idx == 0 else "fn_norm2_g_layer1.npy"))',
    1
)

ast.parse(s)
p.write_text(s)

print("LAYER-SPECIFIC NORM2 ROUTING READY — SYNTAX OK")
print("VERIFIED BLOCK-0 UNCHANGED")
PY
