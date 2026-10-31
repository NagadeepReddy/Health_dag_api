python3 -B - <<'PY'
from pathlib import Path
import re, ast, hashlib

p = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_worker_adapter.py")

if not p.is_file():
    raise SystemExit("STOP: clean worker adapter missing")

source = p.read_text()

fallback = r'Path\(\s*"/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"\s*"real_max_batch2_backend\.py"\s*\),'
old_package = r'Path\(\s*"/application1/cta_max_true_batch_dev_20261028/"\s*"batch2_candidate/cta_max"\s*\)'

updated, a = re.subn(fallback, "", source)
updated, b = re.subn(old_package, 'Path("/batch2/cta_max")', updated)

if (a, b) != (1, 1):
    raise SystemExit(f"STOP: unexpected references: fallback={a}, package={b}; nothing changed")

ast.parse(updated, filename=str(p))
p.write_text(updated)

print("OLD BACKEND FALLBACK REMOVED:", a)
print("CTA_MAX PACKAGE PATH UPDATED:", b)
print("NEW PACKAGE PATH: /batch2/cta_max")
print("PYTHON SYNTAX: PASS")
print("CLEAN WORKER SHA256:", hashlib.sha256(p.read_bytes()).hexdigest())
print("VALIDATED ORIGINAL: UNCHANGED")
PY
