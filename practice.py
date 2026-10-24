cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_context.py")
s = p.read_text()

if "@dataclass\nclass CTAContext" not in s:
    assert s.count("class CTAContext(BaseContext):") == 1
    s = "from dataclasses import dataclass\n" + s
    s = s.replace(
        "class CTAContext(BaseContext):",
        "@dataclass\nclass CTAContext(BaseContext):",
        1
    )
    marker = '"""Native MAX Serve request context carrying real CTA JSON."""'
    assert s.count(marker) == 1
    s = s.replace(
        marker,
        marker + "\n    _request_id: str\n    body: dict\n    _status: GenerationStatus",
        1
    )
    compile(s, str(p), "exec")
    p.write_text(s)

print("CTA DATACLASS ADAPTER: READY")
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
from maxserve_cta_extension.cta_context import CTAContext
from max.interfaces.queue import msgpack_numpy_encoder
import msgspec

data = msgpack_numpy_encoder()(CTAContext("cta-test", {"test": 1}))
print("MAX SERIALIZATION: PASS", len(data))
print("DECODED:", msgspec.msgpack.decode(data))
PY
