python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
src = base / "parallel_transformer_block.py"
dst = base / "parallel_transformer_block_multilayer.py"

s = src.read_text()

old_sig = "def __init__(self, dtype: DType, device: DeviceRef) -> None:"
old_prefix = '"sequence_transformer.ptransformer.0.'

assert s.count(old_sig) == 1, "STOP: constructor differs"
assert s.count(old_prefix) == 3, "STOP: layer weight names differ"
assert not dst.exists(), "STOP: target already exists"

s = s.replace(
    old_sig,
    "def __init__(self, dtype: DType, device: DeviceRef, layer_idx: int = 0) -> None:",
    1
)
s = s.replace(
    old_prefix,
    'f"sequence_transformer.ptransformer.{layer_idx}.'
)

ast.parse(s)
dst.write_text(s)

print("MULTILAYER COPY CREATED — SYNTAX OK")
print("VERIFIED BLOCK-0 UNCHANGED")
PY
