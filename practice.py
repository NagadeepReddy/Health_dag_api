python3 -B - <<'PY'
from pathlib import Path

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")

required = {
    "Original CTA pipeline": "artifacts/v1.168/core-artifact/pipeline.py",
    "Original DS model": "artifacts/v1.168/core-artifact/model_0_base.pt",
    "Native MAX weights": "artifacts/v1.168-max/cta_native_model/cta_real_fp32.safetensors",
    "MAX launcher": "artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_native_launcher.py",
    "MAX worker": "artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_worker_adapter.py",
    "Queue compatibility": "artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_queue_compat.py",
    "Batch-2 backend": "batch2/real_max_batch2_backend.py",
    "CTA test input": "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json",
    "Integration weights": "batch2/cta_max/grecbase_integration_weights/seq_dense.weight.npy",
}

print("=== CLEAN PACKAGE FILE CHECK ===")
missing = []
for label, relative in required.items():
    found = (root / relative).is_file()
    print(("PASS" if found else "MISSING"), label)
    if not found:
        missing.append(relative)

print("\n=== LEGACY DEVELOPMENT PATH CHECK ===")
legacy = []
for folder in (root / "batch2", root / "artifacts/v1.168-max/cta_native_batch2_release_candidate"):
    for p in sorted(folder.rglob("*.py")):
        for n, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            if any(x in line for x in (
                "cta_max_true_batch_dev_20261028",
                "CTA_MAX_TRUE_BATCH2_DEV_20261029",
                "batch2_candidate",
                "/application/"
            )):
                legacy.append(f"{p.relative_to(root)}:{n}: {line.strip()[:140]}")

for item in legacy:
    print("REVIEW:", item)

print("\nMISSING FILES:", len(missing))
print("LEGACY REFERENCES:", len(legacy))
print("READ-ONLY CHECK COMPLETE")
PY
