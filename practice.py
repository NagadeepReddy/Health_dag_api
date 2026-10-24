cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput
from max.interfaces.scheduler import SchedulerResult
from max.serve.queue.zmq_queue import msgpack_numpy_encoder, msgpack_numpy_decoder

try:
    response = {
        "cta-test": SchedulerResult.create(
            CTASerializableOutput(is_done=True, result={"status": "ok"})
        )
    }
    encoded = msgpack_numpy_encoder()(response)
    decoded = msgpack_numpy_decoder(dict)(encoded)
    assert "cta-test" in decoded
    print("CTA FULL RESPONSE WIRE FORMAT: PASS")
    print("ENCODED BYTES:", len(encoded))
except Exception as e:
    print("CTA FULL RESPONSE WIRE FORMAT: FAIL")
    print(type(e).__name__, str(e)[:300])
PY
