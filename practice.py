cd /application1/sajjna8/rt-pzaas-cta-offers-v1

timeout 90s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=4g \
  -v "$PWD:/workspace:Z" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import traceback
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper

print("STARTING REAL CTA FACTORY", flush=True)
try:
    model = CTAFactoryWrapper(lambda: None)()
    print("CTA FACTORY SUCCESS:", type(model).__name__, flush=True)
except BaseException:
    print("ACTUAL CTA FACTORY FAILURE:", flush=True)
    traceback.print_exc()
    raise
PY
