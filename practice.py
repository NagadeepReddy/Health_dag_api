python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")
matches = list(root.rglob("bplan_native_scheduler.py"))
assert len(matches) == 1, f"Expected one scheduler, found {len(matches)}"

p = matches[0]
source = p.read_text()
needle = "self.response_queue.put_nowait(responses)"
marker = "BPLAN RESPONSE SEND START"

if marker not in source:
    assert source.count(needle) == 1, "Unexpected scheduler structure; no changes made"
    backup = p.with_suffix(".py.before_response_trace")
    backup.write_text(source)

    replacement = (
        'print("BPLAN RESPONSE SEND START", '
        '[str(k) for k in responses], flush=True)\n'
        '            ' + needle + '\n'
        '            print("BPLAN RESPONSE SEND COMPLETE", flush=True)'
    )
    updated = source.replace(needle, replacement)
    compile(updated, str(p), "exec")
    p.write_text(updated)

print("BPLAN RESPONSE TRACE INSTALLED:", p)
PY

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

"${P[@]}" restart bplan-debug || exit 1

echo "Waiting for native HTTP route..."
READY=0
for i in $(seq 1 90); do
  CODE=$(curl -s --max-time 2 -o /dev/null -w '%{http_code}' \
    http://127.0.0.1:18768/bplan/predict)
  if [ "$CODE" = "405" ]; then
    READY=1
    break
  fi
  sleep 2
done

if [ "$READY" = 1 ]; then
  echo "=== BPLAN HTTP TEST ==="
  curl -sS --max-time 90 \
    -o /tmp/bplan_response_trace.json \
    -w 'HTTP STATUS: %{http_code}; TIME: %{time_total}s\n' \
    -X POST http://127.0.0.1:18768/bplan/predict \
    -H 'Content-Type: application/json' \
    --data-binary @/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json
  echo "=== RESPONSE ==="
  head -c 500 /tmp/bplan_response_trace.json 2>/dev/null
  echo
else
  echo "BPLAN ROUTE NOT READY"
fi

echo "=== RESPONSE DELIVERY MARKERS ==="
"${P[@]}" logs --tail 300 bplan-debug 2>&1 |
  grep -E 'BPLAN TRACE|BPLAN REAL MAX|BPLAN RESPONSE SEND|Traceback|Error' |
  tail -45
