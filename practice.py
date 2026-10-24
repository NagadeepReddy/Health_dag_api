cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()

old = 'result = getattr(output, "result", None)'

new = '''result = getattr(output, "result", None)
                from .cta_native_scheduler import CTASerializableOutput
                if isinstance(result, CTASerializableOutput):
                    result = result.result'''

if new not in s:
    if s.count(old) != 1:
        raise SystemExit("Expected router code not found. No changes made.")
    s = s.replace(old, new, 1)
    compile(s, str(p), "exec")
    p.write_text(s)

print("CTA HTTP RESPONSE UNWRAP: SYNTAX PASS")
print("ONLY MAX ROUTER MODIFIED")
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
  > /tmp/cta_native_final.log 2>&1

rc=$?

echo "=== CTA RESULTS ==="
grep -E 'CTA RESPONSE:|CTA NATIVE HTTP STATUS|CTA NATIVE END-TO-END|CTA_NATIVE_RESPONSE_TYPES|ValidationError|AssertionError|Traceback|CTA RESPONSE|CTA PROBE' \
  /tmp/cta_native_final.log | tail -15

echo "E2E EXIT CODE: $rc"
