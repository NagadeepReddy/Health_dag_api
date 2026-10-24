cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py")
s = p.read_text()

old = "SimpleNamespace(is_done=True, result=result)"
new = "CTASerializableOutput(is_done=True, result=result)"

if new not in s:
    if old not in s:
        raise SystemExit("Expected response code not found. No changes made.")

    addition = """import msgspec
from typing import Any

class CTASerializableOutput(msgspec.Struct):
    is_done: bool
    result: Any

"""
    s = addition + s.replace(old, new, 1)
    compile(s, str(p), "exec")
    p.write_text(s)

print("CTA RESPONSE SERIALIZATION FIX: SYNTAX PASS")
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
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py

echo "E2E EXIT CODE: $?"
