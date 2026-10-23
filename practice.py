cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

src = Path("artifacts/v1.168-max/maxserve_cta_extension")
out = Path("/tmp/cta_native_extension_review.zip")

with ZipFile(out, "w", ZIP_DEFLATED) as z:
    for p in sorted(src.glob("*.py")):
        z.write(p, p.name)

print("Created:", out)
print("Python files:", len(list(src.glob("*.py"))))
PY
