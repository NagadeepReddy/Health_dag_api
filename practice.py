cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
import json
from pathlib import Path

source = Path("artifacts/v1.168/config/config.json")
target = Path("artifacts/v1.168-max/cta_native_model/config.json")

data = json.loads(source.read_text())
data["architectures"] = ["CTAMaxPipelineModel"]

target.parent.mkdir(parents=True, exist_ok=True)
if target.exists():
    print("Existing native config preserved:", target)
else:
    target.write_text(json.dumps(data, indent=2) + "\n")
    print("CTA NATIVE CONFIG CREATED:", target)

print("Original DS config unchanged")
PY
