cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import re

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()

if "from max.interfaces.request import RequestID" not in s:
    s = s.replace(
        "from .cta_context import CTAContext",
        "from .cta_context import CTAContext\n"
        "    from max.interfaces.request import RequestID",
        1
    )

s, count = re.subn(
    r'(with queue\.open_channel\(\s*)request_id(?=\s*,)',
    r'\1(RequestID(request_id) if not isinstance(request_id, RequestID) else request_id)',
    s
)

assert count == 1 or "RequestID(request_id) if not isinstance" in s
compile(s, str(p), "exec")
p.write_text(s)

print("CTA HTTP REQUEST-ID MATCHING: FIXED")
print("ORIGINAL DS CODE: UNCHANGED")
PY

timeout -k 5s 90s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
  > /tmp/cta_id_match_test.log 2>&1

rc=$?
echo "=== NATIVE CTA RESULT ==="
grep -E 'CTA NATIVE HTTP STATUS|CTA RESPONSE:|CTA WORKER RESPONSE IDS: \[.|ValidationError|Traceback|Error' \
  /tmp/cta_id_match_test.log | tail -10
echo "EXIT CODE: $rc"
