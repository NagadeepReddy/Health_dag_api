cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py")
s = p.read_text()

old = "self.response_queue.put_nowait(responses)"
marker = "CTA_NATIVE_RESPONSE_TYPES:"

if marker not in s:
    assert old in s, "Expected response queue call not found. No changes made."

    replacement = """print(
            "CTA_NATIVE_RESPONSE_TYPES:",
            type(responses).__name__,
            [
                (
                    type(value).__name__,
                    type(getattr(value, "result", None)).__name__
                )
                for value in responses.values()
            ],
            flush=True,
        )
        self.response_queue.put_nowait(responses)"""

    s = s.replace(old, replacement, 1)
    compile(s, str(p), "exec")
    p.write_text(s)

print("CTA RESPONSE DIAGNOSTIC: INSTALLED")
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
  2>&1 | tee /tmp/cta_native_response_debug.log

echo "=== IMPORTANT RESULTS ==="
grep -E 'CTA_NATIVE_RESPONSE_TYPES|CTA RESPONSE:|CTA NATIVE HTTP STATUS:|ValidationError|RecursionError|CTA NATIVE END-TO-END|Worker failed' \
  /tmp/cta_native_response_debug.log | tail -15
