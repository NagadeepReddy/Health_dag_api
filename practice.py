cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none --memory=8g \
  -v "$PWD:/workspace:Z" -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import json
from pathlib import Path
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper

body = json.loads(Path("artifacts/v1.167/samples/sanity_input.json").read_text())

def fix_nulls(obj):
    count = 0
    if isinstance(obj, dict):
        if "webinteraction_name" in obj and obj["webinteraction_name"] is None:
            obj["webinteraction_name"] = ""
            count += 1
        for value in obj.values():
            count += fix_nulls(value)
    elif isinstance(obj, list):
        for value in obj:
            count += fix_nulls(value)
    return count

print("Corrected null test fields:", fix_nulls(body), flush=True)
pipeline = CTAFactoryWrapper(None)()
result = pipeline.cta_adapter.predict(body)
print("CTA NATIVE WORKER PREDICTION PASS")
print(json.dumps(result, default=str)[:1500])
PY
