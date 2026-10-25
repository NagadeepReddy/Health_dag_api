cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none --memory=4g \
-v "$PWD:/workspace:Z" -w /workspace \
-e PYTHONPATH=/workspace/artifacts/v1.168-max \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
import inspect
from max.serve.pipelines.model_worker import ModelWorker
from maxserve_cta_extension.cta_worker_registration import install_cta_scheduler_hook

install_cta_scheduler_hook()
g = inspect.unwrap(ModelWorker.run).__globals__
f = g.get("load_scheduler")

print("SCHEDULER FUNCTION:", getattr(f, "__name__", None))
print("CTA HOOK ACTIVE:", bool(f and f.__globals__.get("_cta_hook")))
'
