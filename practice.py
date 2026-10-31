python3 -B - <<'PY'
from pathlib import Path

p = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_worker_adapter.py")

print("=== CLEAN WORKER ADAPTER: LINES 75-115 ===")
if not p.is_file():
    raise SystemExit("STOP: clean worker adapter missing")

lines = p.read_text().splitlines()
for n in range(75, min(116, len(lines) + 1)):
    print(f"{n}: {lines[n-1]}")

print("READ-ONLY CHECK COMPLETE")
PY
