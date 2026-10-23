cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --network=none --memory=6g --cpus=2 \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import sys
from pathlib import Path

root = Path("/workspace/artifacts/v1.168")
sys.path.insert(0, str(root / "core-artifact"))

from pipeline import pipeline as CTA
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper

print("CREATING REAL CTA PIPELINE", flush=True)

p = CTAFactoryWrapper(CTA)()

assert isinstance(p, CTA)
assert p.cta_native_pipeline is True
assert p.cta_adapter is not None

print("REAL CTA FACTORY: PASS", flush=True)
print("CTA NATIVE PIPELINE: PASS", flush=True)
print("CTA MAX ADAPTER: PASS", flush=True)
PY

echo "EXIT CODE: $?"
