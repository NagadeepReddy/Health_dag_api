python3 - <<'PY'
from pathlib import Path

root = Path("/application1")
repo = root / "sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max"
candidate = root / "cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"
backend = root / "CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py"

for name, path in [
    ("WORKING PACKAGE", repo),
    ("CANDIDATE PACKAGE", candidate),
    ("CANDIDATE CONTRACT", candidate / "run/batch2_contract.py"),
    ("WORKING CONTRACT", repo / "run/batch2_contract.py"),
    ("DEV BACKEND", backend),
]:
    print(f"{name}: {'EXISTS' if path.exists() else 'MISSING'}")
    print(f"  {path}")

if backend.is_file():
    for n, line in enumerate(backend.read_text().splitlines(), 1):
        if "batch2_contract" in line or "pack_two_requests" in line:
            print(f"BACKEND LINE {n}: {line.strip()}")
PY
