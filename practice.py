python3 - <<'PY'
from pathlib import Path
import ast, re, shutil

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
s = p.read_text()

pattern = (
    r'(?m)^[ \t]*causal = np\.triu\(\n'
    r'[ \t]*np\.ones\(\(length, length\), dtype=np\.float32\), 1\n'
    r'[ \t]*\) \* -1\.0e9\n'
    r'[ \t]*scores = scores \+ ops\.constant\(\n'
    r'[ \t]*causal\.reshape\(1, 1, length, length\),\n'
    r'[ \t]*dtype=scores\.dtype, device=DeviceRef\.CPU\(\)\n'
    r'[ \t]*\)\n'
)

matches = list(re.finditer(pattern, s))
assert len(matches) == 1, "STOP: causal block differs; no changes made"

updated = s[:matches[0].start()] + s[matches[0].end():]
ast.parse(updated)

backup = p.with_suffix(".py.before_causal_removal.bak")
shutil.copy2(p, backup)
p.write_text(updated)

print("Extra MAX causal mask removed")
print("Python syntax PASS")
print("Original DS code UNCHANGED")
print("Backup:", backup)
PY
