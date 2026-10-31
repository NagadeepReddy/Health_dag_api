python3 -B - <<'PY'
from pathlib import Path
import ast

base = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max")
pkg = base / "cta_max"
ext = base / "cta_native_batch2_release_candidate/maxserve_cta_extension"

required = [
    base / "real_max_batch2_backend.py",
    pkg / "run_batch2_contract.py",
    pkg / "run_real_sanity_input_adapter.py",
    pkg / "grecbase_fusion_full_head_72_max.py",
    ext / "cta_worker_adapter.py",
    ext / "cta_native_launcher.py",
]

bad_paths = [
    "/application1/cta_max_true_batch_dev_20261028",
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029",
    "/batch2/cta_max",
    "/batch2/real_max_batch2_backend.py",
]

print("=== REQUIRED RUNTIME FILES ===")
missing = []
for p in required:
    ok = p.is_file()
    print("PASS" if ok else "MISSING", p.relative_to(base))
    if not ok:
        missing.append(str(p))

print("\n=== CLEAN PYTHON SOURCE AUDIT ===")
files = sorted(base.rglob("*.py"))
syntax_errors = []
stale = []

for p in files:
    if "__pycache__" in p.parts:
        continue
    text = p.read_text()
    try:
        ast.parse(text, filename=str(p))
    except SyntaxError as e:
        syntax_errors.append((str(p.relative_to(base)), str(e)))
    for n, line in enumerate(text.splitlines(), 1):
        if any(old in line for old in bad_paths):
            stale.append((str(p.relative_to(base)), n, line.strip()[:160]))

print("PYTHON FILES CHECKED:", len(files))
print("SYNTAX ERRORS:", len(syntax_errors))
print("OLD DEVELOPMENT REFERENCES:", len(stale))
print("MISSING REQUIRED FILES:", len(missing))

for item in syntax_errors:
    print("SYNTAX ERROR:", item)
for item in stale:
    print("OLD REFERENCE:", item)
for item in missing:
    print("MISSING:", item)

print("\nSTATIC AUDIT:", "PASS" if not (missing or syntax_errors or stale) else "REVIEW REQUIRED")
print("ORIGINAL FILES: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("READ-ONLY CHECK COMPLETE")
PY
