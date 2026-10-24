cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py")
s = p.read_text()

lines = [
    line for line in s.splitlines(keepends=True)
    if "from maxserve_cta_extension.cta_architecture_registration import register_cta_architecture" not in line
    and "register_cta_architecture()" not in line
]

if len(lines) == len(s.splitlines(keepends=True)):
    print("TEMPORARY BRIDGE ALREADY DISCONNECTED")
else:
    p.write_text("".join(lines))
    print("INCOMPATIBLE LLAMA BRIDGE DISCONNECTED")

PY

python3 -m py_compile \
  artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
  && echo "NATIVE LAUNCHER SYNTAX PASS"
