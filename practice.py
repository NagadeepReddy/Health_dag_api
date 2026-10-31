python3 -B - <<'PY'
from pathlib import Path
import shutil

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
dst = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts")

items = [
    (repo / "artifacts/v1.168", dst / "v1.168"),
    (repo / "artifacts/v1.168-max/cta_native_model",
     dst / "v1.168-max/cta_native_model"),
]

if not (dst / "v1.168-max/cta_native_batch2_release_candidate/CTA_NATIVE_BATCH2_CPU_ACCEPTANCE_20261030.json").is_file():
    raise SystemExit("STOP: validated release missing")

for src, target in items:
    if not src.is_dir() or target.exists():
        raise SystemExit(f"STOP: missing source or existing destination: {target}")

required = sum(
    p.stat().st_size
    for src, _ in items
    for p in src.rglob("*")
    if p.is_file() and "__pycache__" not in p.parts
)

available = shutil.disk_usage(dst).free
if available < required * 2:
    raise SystemExit("STOP: insufficient free space")

for src, target in items:
    shutil.copytree(src, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print("COPIED:", target)

print("ORIGINAL FILES: UNCHANGED")
print("NEXT: VERIFY COPIED DEPENDENCIES")
PY
