cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import re

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()

pattern = (
    r'(?m)^([ \t]*)result = getattr\(output, "result", None\)\n'
    r'[ \t]*from \.cta_native_scheduler import CTASerializableOutput\n'
    r'[ \t]*if isinstance\(result, CTASerializableOutput\):\n'
    r'[ \t]*result = result\.result\n'
)

def fix(m):
    indent = m.group(1)
    return (
        indent + 'result = getattr(output, "result", None)\n'
        + indent + 'result = getattr(result, "result", result)\n'
    )

updated, count = re.subn(pattern, fix, s)

if count != 1:
    raise SystemExit("Expected block not found. No changes made.")

compile(updated, str(p), "exec")
p.write_text(updated)

print("CTA ROUTER INDENTATION FIX: PASS")
print("CTA RESPONSE UNWRAPPING: INSTALLED")
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
  > /tmp/cta_native_final.log 2>&1

rc=$?

echo "=== CTA RESULTS ==="
grep -E 'CTA PROBE|CTA NATIVE HTTP STATUS|CTA RESPONSE:|CTA NATIVE END-TO-END|SyntaxError|ValidationError|AssertionError|Traceback' \
  /tmp/cta_native_final.log | tail -15

echo "E2E EXIT CODE: $rc"
