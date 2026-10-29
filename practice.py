cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path

base = Path("/application1/cta_max_true_batch_dev_20261028")
candidate = Path("/application1/cta_max_native_release_candidate_20261028")

files = {
    "BENCHMARK": base / "native_concurrent2_static.py",
    "HELPER": base / "cta_native_benchmark_helper.py",
    "ROUTER": candidate / "cta_router.py",
    "E2E TEST": candidate / "cta_native_e2e_test.py",
}

for label, path in files.items():
    print(f"\n=== {label} ===")
    if not path.is_file():
        print("MISSING:", path)
        continue
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines, 1):
        if any(x in line for x in (
            "import ", "timeout(", "timeout=",
            "wait_for(", "504", "120", "300",
            "register_cta_routes", "create_app"
        )):
            print(f"{i}: {line.strip()[:180]}")

print("\nCHECK COMPLETE — NO FILES MODIFIED")
print("MAX NOT STARTED")
PY
