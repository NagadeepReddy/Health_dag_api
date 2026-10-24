cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
from max.interfaces.request import RequestID
from max.interfaces.scheduler import SchedulerResult
from max.serve.queue.zmq_queue import msgpack_numpy_encoder, msgpack_numpy_decoder
from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

contract = dict[RequestID, SchedulerResult[CTASerializableOutput]]
rid = RequestID("cta-test")
response = {
    rid: SchedulerResult.create(
        CTASerializableOutput(is_done=True, result={"status": "ok"})
    )
}

try:
    wire = msgpack_numpy_encoder()(response)
    decoded = msgpack_numpy_decoder(contract)(wire)
    assert decoded[rid].result.result == {"status": "ok"}
    print("CTA MAX TYPED RESPONSE CONTRACT: PASS")
except Exception as e:
    print("CTA MAX TYPED RESPONSE CONTRACT: FAIL")
    print(type(e).__name__, str(e)[:300])
PY
