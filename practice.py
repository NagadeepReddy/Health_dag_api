python3 -B - <<'PY'
from pathlib import Path
import ast, hashlib

p = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/batch2/real_max_batch2_backend.py")
old = "/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"
new = "/batch2/cta_max"

if not p.is_file():
    raise SystemExit("STOP: clean backend missing")

source = p.read_text()
count = source.count(old)
if count == 0:
    raise SystemExit("STOP: expected old path not found; nothing changed")

updated = source.replace(old, new)
ast.parse(updated, filename=str(p))

p.write_text(updated)
print("CLEAN BACKEND PATHS UPDATED:", count)
print("NEW PATH:", new)
print("PYTHON SYNTAX: PASS")
print("ORIGINAL BACKEND: UNCHANGED")
print("CLEAN BACKEND SHA256:", hashlib.sha256(p.read_bytes()).hexdigest())
PY
