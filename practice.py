cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py")
s = p.read_text()

anchor = "self.response_queue.put_nowait(responses)"
assert s.count(anchor) == 1, "Expected response send not found"

if "CTA WORKER RESPONSE IDS:" not in s:
    lines = s.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if anchor in line:
            indent = line[:len(line) - len(line.lstrip())]
            lines.insert(
                i,
                indent + 'print("CTA WORKER RESPONSE IDS:", list(responses.keys()), flush=True)\n'
            )
            break
    updated = "".join(lines)
    compile(updated, str(p), "exec")
    p.write_text(updated)

print("CTA WORKER RESPONSE TRACE: READY")
print("DS CODE: UNCHANGED")
PY

timeout 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
  > /tmp/cta_response_ids.log 2>&1

echo "=== RESPONSE ID CHECK ==="
grep -E 'CTA HTTP FANOUT|CTA WORKER RESPONSE IDS|CTA NATIVE HTTP STATUS|CTA RESPONSE:|Traceback' \
  /tmp/cta_response_ids.log | tail -10
