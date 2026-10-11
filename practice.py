python - <<'PY'
from pathlib import Path
import ast
import re

p = Path("artifacts/v1.168-max/cta_max/run_transformer_layer1.py")
s = p.read_text()

pattern = r'(weights\[\s*["\']sequence_transformer\.ptransformer\.)0(\.[^"\']+["\']\s*\])'

updated, count = re.subn(
    pattern,
    lambda m: m.group(1) + "1" + m.group(2),
    s
)

print("REGISTRY KEYS FOUND:", count)
assert count == 5, f"STOP: expected 5, found {count}"

ast.parse(updated)
p.write_text(updated)

print("BLOCK-1 REGISTRY FIXED — SYNTAX OK")
print("BLOCK-0 AND DS CODE UNCHANGED")
PY
