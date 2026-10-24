cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_native_model/__init__.py")
if p.exists():
    print("Existing architecture package preserved:", p)
else:
    p.write_text(
        '"""Native CTA architecture for Modular MAX."""\n'
        'from .arch import cta_arch\n\n'
        'ARCHITECTURES = [cta_arch]\n'
    )
    print("CTA ARCHITECTURE PACKAGE CREATED")
PY
