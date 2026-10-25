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
f = g["load_scheduler"]

print("PATCHED FUNCTION:", f.__name__)
print("CTA SELECTION LOGIC:", "_cta_native_pipeline" in inspect.getsource(f))
print("CTA SCHEDULER REFERENCE:", "create_cta_scheduler" in inspect.getsource(f))
'
