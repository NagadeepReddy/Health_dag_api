cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/maxserve_cta_extension")
p = base / "cta_context.py"
q = base / "cta_native_scheduler.py"
a, b = p.read_text(), q.read_text()

if "wire_request_id: str" not in a:
    assert "    body: dict\n" in a
    assert "self._request_id = request_id" in a
    a = a.replace("    body: dict\n",
                  "    body: dict\n    wire_request_id: str\n", 1)
    a = a.replace("self._request_id = request_id",
                  "self._request_id = request_id\n        self.wire_request_id = request_id", 1)

old = 'CTAContext(context["request_id"], context["body"])'
new = 'CTAContext(context["wire_request_id"], context["body"])'
if old in b:
    b = b.replace(old, new, 1)
else:
    assert new in b, "Scheduler anchor not found"

compile(a, str(p), "exec")
compile(b, str(q), "exec")
p.write_text(a)
q.write_text(b)
print("CTA WIRE REQUEST ID FIX: INSTALLED")
print("ORIGINAL DS CODE: UNCHANGED")
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
from maxserve_cta_extension.cta_context import CTAContext
from max.serve.queue.zmq_queue import msgpack_numpy_encoder, msgpack_numpy_decoder

wire = msgpack_numpy_encoder()(CTAContext("cta-test", {"test": 1}))
decoded = msgpack_numpy_decoder(dict)(wire)
assert decoded["wire_request_id"] == "cta-test"
assert decoded["body"] == {"test": 1}
print("CTA WORKER REQUEST ID ROUNDTRIP: PASS")
PY
