python3 -B - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max")
release = root / "cta_native_batch2_release_candidate"

files = {
    "Acceptance report": release / "CTA_NATIVE_BATCH2_CPU_ACCEPTANCE_20261030.json",
    "Native launcher": release / "maxserve_cta_extension/cta_native_launcher.py",
    "Worker adapter": release / "maxserve_cta_extension/cta_worker_adapter.py",
    "Queue compatibility": release / "maxserve_cta_extension/cta_queue_compat.py",
    "Native model": root / "cta_native_model",
    "CTA JSON input": root / "cta_native_adjusted_sanity_input.json",
    "Real MAX Batch-2 backend": Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py"),
}

print("=== PRESERVED BATCH-2 RELEASE ===")
for name, path in files.items():
    print(f"{name}: {'PRESENT' if path.exists() else 'MISSING'}")
    print(f"  {path}")

print("READ-ONLY CHECK COMPLETE")
PY
