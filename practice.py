python3 -B - <<'PY'
from pathlib import Path

p = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/batch2/cta_max/grecbase_fusion_full_head_72_max.py")
lines = p.read_text().splitlines()

print("=== DYNAMIC IMPORT REVIEW ===")
for n in range(25, min(51, len(lines) + 1)):
    print(f"{n}: {lines[n-1]}")

print("READ-ONLY CHECK COMPLETE")
PY
