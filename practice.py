python3 -B - <<'PY'
from pathlib import Path

base = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max")
p = base / "real_max_batch2_backend.py"

assert p.is_file(), "STOP: clean backend missing"
lines = p.read_text().splitlines()

print("=== BACKEND PATH AND IMPORT LOGIC ===")
for n in range(1, min(125, len(lines)) + 1):
    print(f"{n}: {lines[n-1]}")

print("\n=== REQUIRED MODULE AVAILABILITY ===")
for name in [
    "run_batch2_contract.py",
    "run_real_sanity_input_adapter.py",
    "grecbase_fusion_full_head_72_max.py",
]:
    q = base / "cta_max" / name
    print("FOUND" if q.is_file() else "MISSING", name)

print("\nORIGINAL FILES: UNCHANGED")
print("READ-ONLY CHECK COMPLETE")
PY
