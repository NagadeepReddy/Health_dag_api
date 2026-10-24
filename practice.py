cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import py_compile

pkg = Path("artifacts/v1.168-max/cta_native_model")
init = pkg / "__init__.py"
arch = pkg / "arch.py"

s = init.read_text()
old = "from .arch import cta_arch"
new = "from . import arch"

assert arch.is_file(), "arch.py missing"
assert "register_cta_architecture()" in arch.read_text()
assert old in s, "Expected import not found; no changes made"

init.write_text(s.replace(old, new, 1))

py_compile.compile(str(init), doraise=True)
py_compile.compile(str(arch), doraise=True)

print("CTA ARCH IMPORT FIX: PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY
