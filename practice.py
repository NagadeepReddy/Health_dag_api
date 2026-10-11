python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
src = base / "run_transformer_pytorch_intermediate.py"
dst = base / "run_transformer_pytorch_layer1_ff.py"

s = src.read_text()

old = "sequence_transformer.ptransformer.0.fn."
ref = "transformer_pytorch_output.npy"

assert s.count(old) == 1, "STOP: checkpoint prefix differs"
assert s.count(ref) == 1, "STOP: output path differs"
assert not dst.exists(), "STOP: diagnostic already exists"

s = s.replace(old, "sequence_transformer.ptransformer.1.fn.", 1)
s = s.replace(ref, "transformer_pytorch_layer1_ff.npy", 1)

ast.parse(s)
dst.write_text(s)

print("BLOCK-1 PT DIAGNOSTIC READY — SYNTAX OK")
print("ORIGINAL DIAGNOSTICS AND DS CODE UNCHANGED")
PY
