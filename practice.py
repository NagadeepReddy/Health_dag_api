python3 -B - <<'PY'
from pathlib import Path

clean = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
original = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate")
code = clean / "batch2/cta_max/grecbase_fusion_full_head_72_max.py"

print("=== WEIGHT DEPENDENCY CHECK ===")
for root in (original, clean):
    print("\nROOT:", root)
    for p in sorted(root.rglob("seq_dense.weight.npy")):
        print("FOUND:", p, "| bytes:", p.stat().st_size)

model = clean / "artifacts/v1.168/core-artifact/model_0_base.pt"
print("\nORIGINAL MODEL WEIGHT:", "FOUND" if model.is_file() else "MISSING")

print("\n=== PATH DEFINITIONS ===")
for n, line in enumerate(code.read_text().splitlines(), 1):
    if any(t in line for t in ("WDIR", "BASE", "seq_dense.weight", "model_0_base.pt")):
        print(f"{n}: {line[:180]}")

print("\nREAD-ONLY CHECK COMPLETE")
PY
