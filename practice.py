cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout -k 5s 90s podman \
--root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
-v "$PWD:/workspace:ro" -w /workspace \
-e PYTHONPATH=/workspace/artifacts/v1.168-max \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u -c '
import traceback
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper

print("CTA FACTORY START", flush=True)
try:
    model = CTAFactoryWrapper(None)()
    print("CTA FACTORY RETURNED:", type(model).__name__, flush=True)
    print("CTA PIPELINE FLAG:", getattr(model, "_cta_native_pipeline", None))
    print("CTA ADAPTER:", type(getattr(model, "_cta_adapter", None)).__name__)
except BaseException:
    traceback.print_exc()
    raise
'
