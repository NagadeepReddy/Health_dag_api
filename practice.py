python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block.py")
s = p.read_text()

# Require the exact existing structure.
assert s.count("from max.graph import DeviceRef, TensorValue, ops") == 1
assert s.count("self.norm1 = RMSNorm(") == 1
assert s.count("self.norm2 = RMSNorm(") == 1
assert s.count("x_norm = self.norm1(x)") == 1
assert s.count("ff = self.norm2(ff)") == 1

import re

# Remove the two RMSNorm constructor blocks.
pattern = r"        self\.norm[12] = RMSNorm\(\s*\d+,\s*dtype=dtype,\s*eps=1e-6,\s*\)"
assert len(re.findall(pattern, s)) == 2

s = re.sub(pattern, "", s)

s = s.replace(
    "from max.graph import DeviceRef, TensorValue, ops",
    "from max.graph import DeviceRef, TensorValue, Weight, ops",
    1,
)

anchor = "        self.scale = 256 ** -0.5"
assert s.count(anchor) == 1

s = s.replace(
    anchor,
    '''        self.norm1_weight = Weight(
            "sequence_transformer.ptransformer.0.norm1.weight",
            dtype, [256], device=device,
        )
        self.norm2_weight = Weight(
            "sequence_transformer.ptransformer.0.norm2.weight",
            dtype, [2048], device=device,
        )
''' + anchor,
    1,
)

s = s.replace(
    "x_norm = self.norm1(x)",
    "x_norm = x * ops.rsqrt(ops.mean(x * x, axis=-1, keepdims=True) + 1e-6) * self.norm1_weight",
    1,
)

s = s.replace(
    "ff = self.norm2(ff)",
    "ff = ff * ops.rsqrt(ops.mean(ff * ff, axis=-1, keepdims=True) + 1e-6) * self.norm2_weight",
    1,
)

compile(s, str(p), "exec")
p.write_text(s)
print("NORM WEIGHT FIX APPLIED - SYNTAX CLEAN")
PY
