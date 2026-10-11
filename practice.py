python - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/run_transformer_layer1.py")
s = p.read_text()

old = "sequence_transformer.ptransformer.0."
new = "sequence_transformer.ptransformer.1."

count = s.count(old)
print("BLOCK-0 NAME REFERENCES:", count)

assert count == 5, f"STOP: expected 5 registry names, found {count}"

updated = s.replace(old, new)
ast.parse(updated)
p.write_text(updated)

print("BLOCK-1 REGISTRY NAMES FIXED — SYNTAX OK")
print("BLOCK-0 AND DS CODE UNCHANGED")
PY
