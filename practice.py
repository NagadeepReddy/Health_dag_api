cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py")
s = p.read_text()

old = "    self.request_queue_config = _cta_queues.ZmqConfig[Any](Any)"

new = """    self.request_queue_config = _cta_queues.ZmqConfig[Any](Any)

    from max.interfaces.scheduler import SchedulerResult
    from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

    response_type = dict[str, SchedulerResult[CTASerializableOutput]]
    self.response_queue_config = _cta_queues.ZmqConfig[response_type](
        response_type
    )"""

if "SchedulerResult[CTASerializableOutput]" not in s:
    if old not in s:
        raise SystemExit("Expected queue patch not found. No changes made.")

    updated = s.replace(old, new, 1)
    compile(updated, str(p), "exec")
    p.write_text(updated)

print("CTA RESPONSE QUEUE TYPE FIX: SYNTAX PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY

timeout 150s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
  > /tmp/cta_native_e2e_result.log 2>&1

rc=$?

echo "=== CTA NATIVE E2E RESULTS ==="
grep -E 'CTA_NATIVE_RESPONSE_TYPES|CTA NATIVE HTTP STATUS|CTA RESPONSE:|CTA NATIVE END-TO-END|ValidationError|RecursionError|Exception:|AssertionError|Traceback' \
  /tmp/cta_native_e2e_result.log | tail -20

echo "E2E EXIT CODE: $rc"
