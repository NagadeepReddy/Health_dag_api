cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import py_compile

base = Path("artifacts/v1.168-max")
reg = base / "maxserve_cta_extension/cta_architecture_registration.py"
arch = base / "cta_native_model/arch.py"
init = base / "cta_native_model/__init__.py"

s = reg.read_text()
assert "PIPELINE_REGISTRY.register(cta_arch, allow_override=True)" in s
assert "return cta_arch" not in s
s = s.replace(
    'print("CTA REGISTRY BRIDGE INSTALLED", flush=True)',
    'print("CTA REGISTRY BRIDGE INSTALLED", flush=True)\n    return cta_arch'
)
assert "return cta_arch" in s
reg.write_text(s)

s = arch.read_text()
assert "register_cta_architecture()" in s
arch.write_text(s.replace(
    "register_cta_architecture()",
    "cta_arch = register_cta_architecture()"
))

s = init.read_text()
assert "from . import arch" in s
init.write_text(s.replace(
    "from . import arch",
    "from .arch import cta_arch"
))

for p in (reg, arch, init):
    py_compile.compile(str(p), doraise=True)

print("CTA ARCH EXPORT FIX: PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY
