cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run -i --rm --pull=never \
  --network=none --read-only \
  --memory=512m --pids-limit=32 \
  -v "$PWD":/workspace:ro \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  -e PYTHONDONTWRITEBYTECODE=1 \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local -B - <<'PY'
from max.serve.queue.zmq_queue import (
    msgpack_numpy_encoder,
    msgpack_numpy_decoder,
)
from max.interfaces.request import RequestID
from max.interfaces.scheduler import SchedulerResult
from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

response_type = dict[RequestID, SchedulerResult[CTASerializableOutput]]

payload = {
    RequestID("cta-test-1"): SchedulerResult.create(
        CTASerializableOutput(
            is_done=True,
            result={"status": "ok", "items": [1, 2]}
        )
    )
}

encoded = msgpack_numpy_encoder()(payload)
decoded = msgpack_numpy_decoder(response_type)(encoded)

assert len(decoded) == 1
output = next(iter(decoded.values())).result
assert output.is_done is True
assert output.result == {"status": "ok", "items": [1, 2]}

print("CTA RESPONSE SERIALIZATION: PASS")
print("ENCODED BYTES:", len(encoded))
print("MAX STARTUP: NOT PERFORMED")
print("DS CODE: UNCHANGED")
PY
