python3 - <<'PY'
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_router.py")
s = p.read_text()

changes = [
    (
        '    body = await request.json()\n',
        '    body = await request.json()\n'
        '    print("BPLAN TRACE: POST RECEIVED", flush=True)\n'
    ),
    (
        '    request_id = str(getattr(request.state, "request_id", None) or uuid4())\n',
        '    request_id = str(getattr(request.state, "request_id", None) or uuid4())\n'
        '    print("BPLAN TRACE: QUEUE READY", request_id, flush=True)\n'
    ),
    (
        '                    output = await response_queue.get()\n',
        '                    output = await response_queue.get()\n'
        '                    print("BPLAN TRACE: RESPONSE RECEIVED", request_id, flush=True)\n'
    )
]

if "BPLAN TRACE: POST RECEIVED" in s:
    print("BPLAN ROUTE TRACING: ALREADY INSTALLED")
else:
    for old, new in changes:
        if s.count(old) != 1:
            raise SystemExit(f"STOP: Expected location not unique: {old.strip()}")
        s = s.replace(old, new, 1)
    compile(s, str(p), "exec")
    p.write_text(s)
    print("BPLAN ROUTE TRACING: INSTALLED")

print("BPLAN SYNTAX: PASS")
PY

ROOT=/application1/sajjna8/rt-pzai-bplan-v1
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

"${P[@]}" rm -f bplan-debug 2>/dev/null || true

"${P[@]}" run -d --name bplan-debug --pull=never \
  --network=host -v "$ROOT:/workspace:ro" -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension:/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python localhost/cta-max-faiss:local \
  -m bplan_native_serve_dev.bplan_native_launcher || exit 1

echo "=== WAIT FOR SERVER ==="
READY=0
for i in $(seq 1 120); do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 \
    http://127.0.0.1:18768/bplan/predict)
  if [ "$CODE" = 405 ]; then READY=1; break; fi
  sleep 1
done

if [ "$READY" = 1 ]; then
  echo "=== MYPLAN REQUEST TRACE ==="
  curl -sS --max-time 35 \
    -o /tmp/bplan_myplan_trace.json \
    -w 'HTTP STATUS: %{http_code}\n' \
    -H 'Content-Type: application/json' \
    --data-binary @"$ROOT/artifacts/v1.113/core-artifact/test_samples/test_sample_myplan_bundle.json" \
    http://127.0.0.1:18768/bplan/predict
else
  echo "SERVER NOT READY"
fi

echo "=== TRACE RESULTS ==="
"${P[@]}" logs --tail 400 bplan-debug 2>&1 |
  grep -E 'BPLAN TRACE|BPLAN REAL MAX|BPLAN SPAWN|BPLAN FACTORY|BPLAN RESPONSE SOCKET|BPLAN RESPONSE ID MATCH|worker failed|Error in background|POST /bplan' |
  tail -40
