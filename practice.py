python3 -B - <<'PY'
from pathlib import Path

p = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py")
candidate = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")

print("=== BACKEND IMPORT AND SAFETY CHECK ===")
if not p.is_file():
    raise SystemExit("STOP: Backend missing")

for i, line in enumerate(p.read_text().splitlines()[:75], 1):
    print(f"{i:3}: {line}")

print("\n=== CORRECTED TRANSFORMER ===")
q = candidate / "parallel_transformer_block_2layers.py"
print("Candidate exists:", q.is_file())
print("Expected source:", q)

print("\nREAD ONLY: PASS")
print("CONTAINERS RESTARTED: NONE")
PY
