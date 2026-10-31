CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

CLEAN="$CLEAN" python3 -B - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["CLEAN"])
required = {
    "Model weights": "artifacts/v1.168-max/cta_max/sequence_weights/fn_norm1_g.npy",
    "CTA backend": "artifacts/v1.168-max/real_max_batch2_backend.py",
    "MAX launcher": "artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_native_launcher.py",
    "Worker adapter": "artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_worker_adapter.py",
    "Original pipeline": "artifacts/v1.168/core-artifact/pipeline.py",
}

print("=== CLEAN VM PORTABILITY CHECK ===")
for label, relative in required.items():
    path = root / relative
    print(f"{label}: {'PASS' if path.is_file() else 'CHECK LOCATION'}")
    if not path.is_file():
        matches = list(root.rglob(Path(relative).name))
        for match in matches[:2]:
            print("  FOUND:", match.relative_to(root))

print("CONTAINERS RESTARTED: NONE")
print("READ-ONLY CHECK COMPLETE")
PY
