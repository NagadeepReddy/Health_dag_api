cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path

p = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/distinct_batch2_execution.log")
assert p.is_file(), f"Missing execution log: {p}"

lines = p.read_text(errors="replace").splitlines()

print("=== DISTINCT REAL CTA BATCH-2 EVIDENCE ===")
print("LOG LINES:", len(lines))

keywords = (
    "DISTINCT", "REAL BATCH", "INPUT", "OUTPUT", "SHAPE",
    "EXECUT", "PASS", "FAIL", "ERROR", "TRACEBACK",
    "DIFF", "PARITY", "COMPIL", "WEIGHT", "SAVED"
)

for line in lines:
    if any(word in line.upper() for word in keywords):
        print(line[:300])

print("\n=== FINAL LOG LINES ===")
for line in lines[-25:]:
    print(line[:300])

print("\nFILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
