cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path

base = Path("/application1/cta_max_true_batch_dev_20261028")
candidate = Path("/application1/cta_max_native_release_candidate_20261028")

files = [
    candidate / "cta_router.py",
    Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py"),
    candidate / "cta_native_e2e_test.py",
    candidate / "cta_spawn_worker.py",
    base / "native_concurrent2_static.py",
]

terms = (
    "timeout", "wait_for", "120", "300",
    "cta_router", "sys.path", "importlib"
)

for p in files:
    print("\nFILE:", p)
    if not p.is_file():
        print("MISSING")
        continue
    for n, line in enumerate(p.read_text().splitlines(), 1):
        if any(term in line for term in terms):
            print(f"{n}: {line[:200]}")

print("\nCHECK COMPLETE — NO FILES MODIFIED")
print("MAX NOT STARTED")
PY
