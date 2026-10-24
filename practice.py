cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none --memory=8g \
  -v "$PWD:/workspace:Z" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  -e modelId=cta-native-smoke \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import json, traceback
from pathlib import Path
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper

body = json.loads(Path("artifacts/v1.167/samples/sanity_input.json").read_text())

def fix(obj):
    if isinstance(obj, dict):
        if obj.get("webinteraction_name") is None:
            obj["webinteraction_name"] = ""
        for k, v in list(obj.items()):
            if k == "category" and v == "Smartphones":
                obj[k] = "Tiles"
            else:
                fix(v)
    elif isinstance(obj, list):
        for v in obj:
            fix(v)

fix(body)

try:
    result = CTAFactoryWrapper(dict)().cta_adapter.predict(body)
    print("CTA FULL INFERENCE: PASS")
    print(json.dumps(result, default=str)[:800])
except Exception:
    print("CTA FULL INFERENCE: FAIL")
    traceback.print_exc(limit=8)
PY
