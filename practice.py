python3 -B - <<'PY'
from pathlib import Path

dev = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")
clean = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max")

assert dev.is_dir() and clean.is_dir(), "STOP: Package directory missing"

dev_files = {p.name for p in dev.glob("*.py")}
clean_files = {p.name for p in clean.glob("*.py")}

missing = sorted(dev_files - clean_files)

print("=== PACKAGE COMPLETENESS AUDIT ===")
print("DEVELOPMENT MODULES:", len(dev_files))
print("CLEAN MODULES:", len(clean_files))
print("MODULES NOT IN CLEAN PACKAGE:", len(missing))

for name in missing:
    print("REVIEW:", name)

print("ORIGINAL CTA: UNCHANGED")
print("FILES COPIED: ZERO")
print("CONTAINERS RESTARTED: NONE")
print("READ-ONLY AUDIT COMPLETE")
PY
