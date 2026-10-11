python - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/cta_max/run_transformer_layer1.py")
s = p.read_text()

old = 'WBASE = BASE + "/sequence_weights"'
assert s.count(old) == 1, "STOP: WBASE differs"

needle = 'weights_registry=weights'
assert s.count(needle) == 1, "STOP: registry call differs"

# Change only the registry keys, not file paths.
import re
updated, count = re.subn(
    r'(weights\[\s*["\'])(sequence_transformer\.ptransformer\.)0(\.[^"\']+["\']\s*\])',
    lambda m: m.group(1) + m.group(2) + "1" + m.group(3),
    s
)

assert count == 5, f"STOP: expected 5 layer keys, found {count}"
ast.parse(updated)
p.write_text(updated)

print("BLOCK-1 REGISTRY KEYS UPDATED — SYNTAX OK")
print("BLOCK-0 AND DS CODE UNCHANGED")
PY
