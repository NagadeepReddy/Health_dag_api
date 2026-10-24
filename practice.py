cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import msgspec
from typing import Any
from max.interfaces.scheduler import SchedulerResult
from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

print("=== CTA RESPONSE SERIALIZATION TEST ===", flush=True)

output = CTASerializableOutput(
    is_done=True,
    result={"status": "CTA test"}
)

response = {
    "cta-test-1": SchedulerResult.create(output)
}

try:
    encoded = msgspec.msgpack.encode(response)
    decoded = msgspec.msgpack.decode(
        encoded,
        type=dict[str, SchedulerResult[Any]]
    )
    print("SERIALIZATION: PASS")
    print("DECODED:", decoded)
except Exception as exc:
    print("SERIALIZATION: FAIL")
    print("ERROR:", type(exc).__name__, str(exc))

print("TEST COMPLETE")
PY
