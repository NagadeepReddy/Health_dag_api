cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import json
from pathlib import Path
import cta_native_model

p = Path("/workspace/artifacts/v1.168-max/cta_native_model/config.json")
config = json.loads(p.read_text())
arches = cta_native_model.ARCHITECTURES

print("CONFIG ARCHITECTURES:", config.get("architectures"))
print("CONFIG MODEL TYPE:", config.get("model_type"))
print("REGISTERED NAMES:", [a.name for a in arches])
print("PIPELINE CLASSES:", [a.pipeline_model.__name__ for a in arches])
print("NAME MATCH:", config.get("architectures", [None])[0] in [a.name for a in arches])
PY
