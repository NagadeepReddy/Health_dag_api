cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import json
from pathlib import Path
from max.interfaces.utils.serialization import msgpack_numpy_encoder
from maxserve_cta_extension.cta_context import CTAContext

body = json.loads(Path(
    "/workspace/artifacts/v1.167/samples/sanity_input.json"
).read_text())

encoder = msgpack_numpy_encoder()
context = CTAContext("cta-test", body)

for name, value in [
    ("CTAContext", context),
    ("Plain JSON envelope", {"request_id": "cta-test", "body": body}),
]:
    try:
        data = encoder(value)
        print(name, "SERIALIZATION PASS", len(data), "bytes")
    except Exception as e:
        print(name, "SERIALIZATION FAIL", type(e).__name__, str(e)[:150])
PY
