cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none --memory=8g \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -c '
import json, traceback
from pathlib import Path
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper

body = json.loads(Path("/workspace/artifacts/v1.167/samples/sanity_input.json").read_text())
fixed = [0]

def adjust(obj):
    if isinstance(obj, dict):
        page = obj.get("page")
        if isinstance(page, dict) and str(page.get("name", "")).lower() == "gridwall_smartphones":
            if obj.get("webinteraction_name") is None:
                obj["webinteraction_name"] = ""
                fixed[0] += 1
        for key, value in obj.items():
            if key == "webinteraction_name" and value is None:
                obj[key] = ""
                fixed[0] += 1
            elif key == "category" and value == "Smartphones":
                obj[key] = "Tiles"
            else:
                adjust(value)
    elif isinstance(obj, list):
        for item in obj:
            adjust(item)

adjust(body)
print("REQUEST FIELDS CORRECTED:", fixed[0], flush=True)

try:
    result = CTAFactoryWrapper(dict)().cta_adapter.predict(body)
    print("CTA INFERENCE: PASS")
    print(json.dumps(result, default=str)[:1000])
except Exception:
    print("CTA INFERENCE: FAIL")
    traceback.print_exc(limit=6)
'
