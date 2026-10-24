cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import re, py_compile

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py")
s = p.read_text()
pattern = r'"--custom-architectures",\s*"/workspace/artifacts/v1\.168-max:cta_native_model",\s*'
updated, count = re.subn(pattern, "", s, count=1)

if count:
    p.write_text(updated)
    py_compile.compile(str(p), doraise=True)
    print("INCOMPLETE ARCHITECTURE FLAG REMOVED — SYNTAX PASS")
else:
    print("FLAG NOT PRESENT — NO CHANGES")
PY
