cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
from maxserve_cta_extension.cta_context import CTAContext
from max.serve.queue.zmq_queue import msgpack_numpy_encoder

ctx = CTAContext("cta-test", {"test": 1})

try:
    data = msgpack_numpy_encoder()(ctx)
    print("MAX SERIALIZATION: PASS", len(data))
except Exception as e:
    print("MAX SERIALIZATION: FAIL", type(e).__name__, str(e)[:200])
PY
