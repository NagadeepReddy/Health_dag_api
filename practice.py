python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
pt_src = base / "run_transformer_parity.py"
pt_dst = base / "run_transformer_parity_layer1.py"
max_runner = base / "run_transformer_layer1.py"

assert pt_src.is_file() and max_runner.is_file()
assert not pt_dst.exists(), "STOP: Block-1 PT runner exists"

pt = pt_src.read_text()
mx = max_runner.read_text()

old_prefix = "sequence_transformer.ptransformer.0.fn."
old_ref = "transformer_pytorch_output.npy"
new_ref = "transformer_pytorch_output_layer1.npy"

assert pt.count(old_prefix) == 1, "STOP: PT prefix differs"
assert pt.count(old_ref) == 1, "STOP: PT output differs"
assert mx.count(old_ref) == 1, "STOP: MAX reference differs"

pt = pt.replace(old_prefix, "sequence_transformer.ptransformer.1.fn.", 1)
pt = pt.replace(old_ref, new_ref, 1)
mx = mx.replace(old_ref, new_ref, 1)

ast.parse(pt)
ast.parse(mx)

pt_dst.write_text(pt)
max_runner.write_text(mx)

print("BLOCK-1 PARITY RUNNERS READY — SYNTAX OK")
print("BLOCK-0 REFERENCE AND DS CODE UNCHANGED")
PY
