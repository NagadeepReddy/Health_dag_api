python3 -B - <<'PY'
from pathlib import Path

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
files = [
    "artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_worker_adapter.py",
    "artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_native_launcher.py",
    "batch2/real_max_batch2_backend.py",
]

for name in files:
    p = root / name
    print("\nFILE:", name)
    if not p.is_file():
        print("MISSING")
        continue
    for number, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
        if any(x in line for x in ("/workspace", "/batch2", "/application1", "backend_file", "model_path")):
            print(f"{number}: {line.strip()[:180]}")

print("\nREAD-ONLY CHECK COMPLETE")
PY
