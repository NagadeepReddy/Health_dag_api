python3 -B - <<'PY'
from pathlib import Path
import shutil, hashlib

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
clean = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")

files = [
    (
        Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py"),
        clean / "batch2/real_max_batch2_backend.py"
    ),
    (
        repo / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json",
        clean / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
    ),
]

for src, dst in files:
    if not src.is_file():
        raise SystemExit(f"STOP: source missing: {src}")
    if dst.exists():
        raise SystemExit(f"STOP: destination already exists: {dst}")

for src, dst in files:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    original = hashlib.sha256(src.read_bytes()).hexdigest()
    copied = hashlib.sha256(dst.read_bytes()).hexdigest()
    if original != copied:
        raise SystemExit(f"FAIL: checksum mismatch: {dst}")

    print("PASS:", dst)

print("ORIGINAL FILES: UNCHANGED")
print("BACKEND AND TEST INPUT: COPIED AND VERIFIED")
PY
