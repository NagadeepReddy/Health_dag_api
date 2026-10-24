cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
import msgspec
from typing import Any
from max.serve.scheduler.base import SchedulerResult
from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

print("=== MAX RESPONSE FORMAT ===", flush=True)
print(inspect.getsource(SchedulerResult), flush=True)

print("\n=== CTA OUTPUT FORMAT ===", flush=True)
print(inspect.signature(CTASerializableOutput), flush=True)

output = CTASerializableOutput(
    is_done=True,
    result={"status": "CTA response test"}
)

response = {
    "cta-test-1": SchedulerResult.create(output)
}

print("\n=== MSGPACK ROUNDTRIP ===", flush=True)

try:
    encoded = msgspec.msgpack.encode(response)
    decoded = msgspec.msgpack.decode(
        encoded,
        type=dict[str, SchedulerResult[Any]]
    )
    print("RESPONSE SERIALIZATION: PASS", flush=True)
    print("DECODED:", decoded, flush=True)
except Exception as exc:
    print("RESPONSE SERIALIZATION: FAIL", flush=True)
    print(type(exc).__name__, str(exc), flush=True)

print("\nORIGINAL DS CODE: UNCHANGED", flush=True)
PY
