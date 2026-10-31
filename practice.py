python3 -B - <<'PY'
from pathlib import Path

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
files = [
    root / "batch2/real_max_batch2_backend.py",
    root / "artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_worker_adapter.py",
    root / "artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_native_launcher.py",
]

for p in files:
    print("\n===", p.name, "===")
    if not p.is_file():
        print("MISSING")
        continue
    for n, line in enumerate(p.read_text().splitlines(), 1):
        if any(x in line for x in (
            "/application1/", "/workspace/", "/batch2/",
            "sys.path", "PYTHONPATH"
        )):
            print(f"{n}: {line.strip()[:160]}")

print("\nCLEAN WEIGHTS:", (root / "batch2/cta_max/grecbase_integration_weights/seq_dense.weight.npy").is_file())
print("READ-ONLY CHECK COMPLETE")
PY
