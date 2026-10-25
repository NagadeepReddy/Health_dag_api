cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
-v "$PWD:/workspace:ro" -w /workspace \
-e CTA_MAX_NATIVE_BOOTSTRAP=1 \
-e PYTHONPATH=/workspace/artifacts/v1.168-max/maxserve_cta_extension/bootstrap:/workspace/artifacts/v1.168-max \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
from max.serve.pipelines.model_worker import ModelWorker

fn = ModelWorker.run.__globals__["load_scheduler"]
print("CTA SCHEDULER HOOK ACTIVE:", getattr(fn, "_cta_hook", False))
print("SCHEDULER FUNCTION:", fn.__name__)
'
