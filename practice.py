python3 -B - <<'PY'
from pathlib import Path
import ast
import re
import os

base = Path(
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
    "native_batch2_minimal_overlay"
)
p = base / "cta_native_scheduler.py"
adapter = base / "cta_worker_adapter.py"

assert p.is_file() and not p.is_symlink(), \
    "STOP: Development scheduler missing"
assert adapter.is_file(), \
    "STOP: Development batch adapter missing"
assert "def predict_batch(" in adapter.read_text(), \
    "STOP: Batch adapter method unavailable"

source = p.read_text()

pattern = (
    r"(?m)^(?P<indent>[ \t]*)"
    r"results = \[self\.adapter\.predict\(active\[0\]\.body\)\]"
    r"[ \t]*$"
)

matches = list(re.finditer(pattern, source))
assert len(matches) == 1, \
    "STOP: Scheduler single-request branch differs"

m = matches[0]
indent = m.group("indent")

lines = [
    "batch_fn = getattr(self.adapter, 'predict_batch', None)",
    "if not callable(batch_fn):",
    "    raise RuntimeError('Real MAX batch backend unavailable')",
    "padded = batch_fn([active[0].body, active[0].body])",
    "if not isinstance(padded, (list, tuple)) or len(padded) != 2:",
    "    raise RuntimeError('Invalid padded MAX batch response')",
    "results = [padded[0]]",
]

replacement = "\n".join(indent + x for x in lines)
updated = source[:m.start()] + replacement + source[m.end():]

ast.parse(updated)

backup = p.with_name(p.name + ".before_single_pad.bak")
assert not backup.exists(), \
    "STOP: Backup already exists"

with backup.open("xb") as f:
    f.write(source.encode())

temp = p.with_name(p.name + ".single_pad.stage")
with temp.open("x") as f:
    f.write(updated)

os.chmod(temp, p.stat().st_mode)
os.replace(temp, p)

assert p.read_text() == updated

print("SINGLE-REQUEST BATCH-2 ADAPTER: STAGED")
print("SYNTAX: PASS")
print("BACKUP: CREATED")
print("ORIGINAL DS: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("LIVE HTTP RETEST: PENDING")
PY
