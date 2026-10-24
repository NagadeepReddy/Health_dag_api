cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()

anchor = 'queue = getattr(pipeline, "_engine_queue", None)'
diagnostic = '''print(
        "CTA QUEUE CONNECTION:",
        "pipeline_type=", type(pipeline).__name__,
        "pipeline_fields=", list(vars(pipeline)) if pipeline is not None else [],
        "app_state=", list(vars(request.app.state).get("_state", {})),
        flush=True,
    )
    '''

if "CTA QUEUE CONNECTION:" not in s:
    assert s.count(anchor) == 1, "Expected queue lookup not found"
    updated = s.replace(anchor, diagnostic + anchor, 1)
    compile(updated, str(p), "exec")
    p.write_text(updated)

print("CTA QUEUE DIAGNOSTIC: READY")
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
  > /tmp/cta_queue_connection.log 2>&1

echo "=== QUEUE CONNECTION RESULT ==="
grep -E 'CTA QUEUE CONNECTION|CTA NATIVE HTTP STATUS|CTA RESPONSE:|Traceback|SyntaxError' \
  /tmp/cta_queue_connection.log | tail -10
