cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max")
pkg = base / "cta_native_model"
reg = base / "maxserve_cta_extension/cta_architecture_registration.py"

assert reg.is_file(), f"Missing registration: {reg}"
assert "def register_cta_architecture(" in reg.read_text(), "Registration function not found"

pkg.mkdir(exist_ok=True)
(pkg / "__init__.py").touch(exist_ok=True)

arch = pkg / "arch.py"
assert not arch.exists(), "arch.py already exists — leaving it unchanged"

arch.write_text(
    "from maxserve_cta_extension.cta_architecture_registration import register_cta_architecture\n"
    "register_cta_architecture()\n"
)

import py_compile
py_compile.compile(str(arch), doraise=True)
print("CTA ARCH MODULE BRIDGE: CREATED — SYNTAX PASS")
PY
