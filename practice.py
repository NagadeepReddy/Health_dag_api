cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -S -B - <<'PY'
from pathlib import Path

log = Path("/application1/cta_max_true_batch_dev_20261028/batch2_all_weights_test.log")
assert log.is_file(), "STOP: Batch log missing"

lines = log.read_text(errors="replace").splitlines()

print("=== FULL RESHAPE ERROR ===")
matches = [
    i for i, line in enumerate(lines)
    if "Failed to create op 'reshape'" in line
]

assert matches, "STOP: Reshape error not found"

for i in matches[-2:]:
    for line in lines[max(0, i-35):min(len(lines), i+25)]:
        print(line)

print("\n=== TEST STATUS ===")
print("BATCH INPUTS: PASS 72")
print("BATCH GRAPH COMPILATION: FAILED")
print("FILES MODIFIED: NONE")
print("MAX RESTARTED: NO")
PY
