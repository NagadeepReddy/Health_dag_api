python - <<'PY'
import json

p = "artifacts/v1.168/config/torch_model_params_base.json"
c = json.load(open(p))

for k, v in c.items():
    if any(x in k.lower() for x in ["head", "transform", "seq", "rotary", "attention"]):
        print(k, "=", v)
PY
