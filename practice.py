cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
adapter = base / "native_batch2/cta_worker_adapter.py"
scheduler = base / "native_batch2/cta_native_scheduler.py"
backend = base / "real_max_batch2_backend.py"
log = base / "real_max_batch2_after_cache_fix.log"

print("=== EXISTING WORK STATUS ===")

for name, path in [
    ("NATIVE ADAPTER", adapter),
    ("NATIVE SCHEDULER", scheduler),
    ("REAL MAX BACKEND", backend),
]:
    print(name, ":", "EXISTS" if path.is_file() else "MISSING")
    if path.is_file():
        ast.parse(path.read_text())

if adapter.is_file():
    tree = ast.parse(adapter.read_text())
    methods = [
        n.name for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef)
    ]
    print("ADAPTER predict_batch:", "PRESENT" if "predict_batch" in methods else "MISSING")

if scheduler.is_file():
    s = scheduler.read_text()
    print("SCHEDULER BATCH DISPATCH:",
          "PRESENT" if "CTA_NATIVE_BATCH_DISPATCH_V1" in s else "MISSING")

if log.is_file():
    evidence = log.read_text()
    print("REAL MAX CPU BATCH-2:",
          "PASS" if "REAL MAX BATCH-2: PASS" in evidence else "UNVERIFIED")

print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
print("ORIGINAL DS CODE: UNCHANGED")
PY
