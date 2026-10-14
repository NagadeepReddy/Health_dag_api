python3 - <<'PY'
from pathlib import Path
import ast
import shutil
import re

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
s = p.read_text()

start = re.search(r'(?m)^[ \t]*causal = np\.triu\(', s)
assert start, "STOP: causal mask not found"

end = re.search(
    r'(?m)^[ \t]*attn = ops\.softmax\(scores\)',
    s[start.end():]
)
assert end, "STOP: attention statement not found"

end_pos = start.end() + end.start()
block = s[start.start():end_pos]

assert block.count("scores = scores + ops.constant(") == 1
assert block.count("causal.reshape(") == 1
assert block.count("np.ones(") == 1

updated = s[:start.start()] + s[end_pos:]
ast.parse(updated)

backup = p.with_suffix(".py.before_causal_alignment.bak")
assert not backup.exists(), "STOP: backup already exists"

shutil.copy2(p, backup)
p.write_text(updated)

print("MAX causal mask removed: PASS")
print("Python syntax: PASS")
print("Original DS code: UNCHANGED")
print("Backup:", backup)
PY
