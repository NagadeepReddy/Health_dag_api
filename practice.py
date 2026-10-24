cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
import json
p = "artifacts/v1.168/config/config.json"
d = json.load(open(p))
print("CONFIG KEYS:", list(d.keys()))
print("MODEL TYPE:", d.get("model_type"))
print("ARCHITECTURES:", d.get("architectures"))
PY
