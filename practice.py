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

expected = dict[str, SchedulerResult[CTASerializableOutput]]
response = {
    "cta-test": SchedulerResult.create(
        CTASerializableOutput(is_done=True, result={"status": "ok"})
    )
}

try:
    decoded = msgpack_numpy_decoder(expected)(
        msgpack_numpy_encoder()(response)
    )
    assert decoded["cta-test"].result.result == {"status": "ok"}
    print("CTA NATIVE RESPONSE DECODE: PASS")
except Exception as e:
    print("CTA NATIVE RESPONSE DECODE: FAIL", type(e).__name__, str(e)[:300])
PY
