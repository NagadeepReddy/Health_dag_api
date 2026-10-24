cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none --memory=8g \
  -v "$PWD:/workspace:Z" -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -c '
import json
from pathlib import Path
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper

pipeline = CTAFactoryWrapper(None)()
body = json.loads(Path("artifacts/v1.167/samples/sanity_input.json").read_text())
result = pipeline.cta_adapter.predict(body)
print("CTA NATIVE WORKER PREDICTION PASS")
print(json.dumps(result, default=str)[:2000])
'
