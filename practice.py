cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
from maxserve_cta_extension.cta_context import CTAContext
from max.serve.queue.zmq_queue import msgpack_numpy_encoder, msgpack_numpy_decoder

original = CTAContext("cta-test", {"test": 1})
encoded = msgpack_numpy_encoder()(original)

try:
    decoded = msgpack_numpy_decoder(CTAContext)(encoded)
    assert isinstance(decoded, CTAContext)
    assert decoded.request_id == "cta-test"
    assert decoded.body == {"test": 1}
    print("MAX CONTEXT ROUNDTRIP: PASS")
except Exception as e:
    print("MAX CONTEXT ROUNDTRIP: FAIL", type(e).__name__, str(e)[:250])
PY
