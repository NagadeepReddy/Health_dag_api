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

def fix(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "webinteraction_name" and v is None:
                obj[k] = ""
            elif k == "category" and v == "Smartphones":
                obj[k] = "Tiles"
            else:
                fix(v)
    elif isinstance(obj, list):
        for item in obj:
            fix(item)

fix(body)
pipeline = CTAFactoryWrapper(dict)()

try:
    result = pipeline.cta_adapter.predict(body)
    print("CTA INFERENCE: PASS")
    print("RESULT:", json.dumps(result, default=str)[:1500])
except Exception:
    print("CTA INFERENCE: FAIL")
    traceback.print_exc(limit=8)
'
