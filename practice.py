cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()

anchor = 'queue = getattr(pipeline, "_engine_queue", None)'
assert s.count(anchor) == 1, "Queue lookup not found; no changes made"

marker = 'CTA ACTUAL ENGINE QUEUE:'
if marker not in s:
    s = s.replace(anchor, anchor + '''
    print(
        "CTA ACTUAL ENGINE QUEUE:",
        "pipeline=", type(pipeline).__name__,
        "queue=", type(queue).__name__,
        "is_none=", queue is None,
        flush=True,
    )''', 1)
    compile(s, str(p), "exec")
    p.write_text(s)

print("CTA QUEUE CHECK INSTALLED")
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
  > /tmp/cta_queue_check.log 2>&1

grep -E 'CTA ACTUAL ENGINE QUEUE|CTA NATIVE HTTP STATUS|CTA RESPONSE:|AssertionError|Traceback' \
  /tmp/cta_queue_check.log | tail -10
