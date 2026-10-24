cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
import json
from pathlib import Path

base = Path("artifacts/v1.168-max")
config = json.loads((base / "cta_native_model/config.json").read_text())

print("CONFIG ARCHITECTURES:", config.get("architectures"), flush=True)
print("CONFIG MODEL TYPE:", config.get("model_type"), flush=True)

p = base / "maxserve_cta_extension/cta_architecture_registration.py"
for n, line in enumerate(p.read_text().splitlines(), 1):
    if any(x in line for x in ("name=", "pipeline_model=", "register(", "return cta_arch")):
        print(f"REGISTRATION LINE {n}: {line.strip()}", flush=True)

print("CHECK COMPLETE", flush=True)
PY
