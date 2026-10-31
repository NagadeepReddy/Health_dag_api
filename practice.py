python3 -B - <<'PY'
from pathlib import Path

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
clean = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")

adapter = clean / "artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_worker_adapter.py"

print("=== CLEAN WORKER ADAPTER: LINES 75-125 ===")
assert adapter.is_file(), "STOP: clean adapter missing"
for n, line in enumerate(adapter.read_text().splitlines(), 1):
    if 75 <= n <= 125:
        print(f"{n}: {line}")

print("\n=== BACKEND SOURCE LOCATIONS ===")
paths = [
    Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py"),
    Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"),
    repo / "artifacts/v1.168-max/cta_max",
    clean / "artifacts/v1.168-max/cta_max",
    clean / "artifacts/v1.168-max/real_max_batch2_backend.py",
]
for p in paths:
    print("FOUND" if p.exists() else "MISSING", p)

print("\nREAD-ONLY CHECK COMPLETE")
PY
