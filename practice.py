python3 -B - <<'PY'
from pathlib import Path

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
base = repo / "artifacts/v1.168-max"

checks = {
    "Original DS pipeline": repo / "artifacts/v1.168/core-artifact/pipeline.py",
    "Original DS model": repo / "artifacts/v1.168/core-artifact/model.py",
    "Native MAX model": base / "cta_native_model",
    "CTA JSON test input": base / "cta_native_adjusted_sanity_input.json",
    "Batch-2 backend": Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py"),
    "Validated release": base / "cta_native_batch2_release_candidate",
}

print("=== EXTERNAL DEPENDENCY CHECK ===")
for name, path in checks.items():
    print(f'{"FOUND" if path.exists() else "MISSING"} | {name} | {path}')

print("READ-ONLY CHECK COMPLETE")
PY
