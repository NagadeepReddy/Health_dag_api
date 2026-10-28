cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path
import shutil
import ast

src = Path("artifacts/v1.168-max/maxserve_cta_extension")
dst = Path("/application1/cta_max_native_release_candidate_20261028")
backup = Path("/application1/cta_max_native_http_pass_20261028.tar.gz")

assert src.is_dir(), "STOP: Integration directory missing"
assert backup.is_file(), "STOP: Working backup missing"
assert not dst.exists(), "STOP: Release candidate already exists"
assert shutil.disk_usage("/application1").free > 1024**3, \
    "STOP: Insufficient free disk space"

files = list(src.rglob("*.py"))
assert files, "STOP: No Python integration files"

for p in files:
    ast.parse(p.read_text())

shutil.copytree(src, dst)

for p in dst.rglob("*.py"):
    ast.parse(p.read_text())

print("RELEASE CANDIDATE COPY: PASS")
print("PYTHON FILES:", len(files))
print("SYNTAX: PASS")
print("LOCATION:", dst)
print("WORKING HTTP 200 IMPLEMENTATION: PRESERVED")
print("ORIGINAL DS CODE: UNCHANGED")
print("CONTAINERS: NOT STARTED")
PY
