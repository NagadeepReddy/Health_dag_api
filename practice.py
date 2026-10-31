python3 -B - <<'PY'
from pathlib import Path

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
files = [
    root / "batch2/real_max_batch2_backend.py",
    root / "artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_worker_adapter.py",
    root / "artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_native_launcher.py",
]

for p in files:
    print(f"\n=== {p.relative_to(root)} ===")
    if not p.is_file():
        print("MISSING")
        continue
    lines = p.read_text(errors="replace").splitlines()
    keywords = ("import ", "from ", "/workspace", "/batch2", "/application1")
    selected = {i for i, line in enumerate(lines) if any(k in line for k in keywords)}
    for i in sorted(selected):
        print(f"{i+1}: {lines[i][:180]}")

print("\nREAD-ONLY DEPENDENCY CHECK COMPLETE")
PY
