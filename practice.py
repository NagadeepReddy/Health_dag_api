cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none --memory=4g \
-v "$PWD:/workspace:Z" -w /workspace \
-e PYTHONPATH=/workspace/artifacts/v1.168-max \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
from max.serve.pipelines import model_worker
from maxserve_cta_extension.cta_worker_registration import install_cta_scheduler_hook
before = model_worker.ModelWorker.run.__globals__.get("load_scheduler")
install_cta_scheduler_hook()
after = model_worker.ModelWorker.run.__globals__.get("load_scheduler")
print("HOOK REPLACED:", before is not after)
print("HOOK NAME:", getattr(after, "__name__", None))
print("HOOK MARKER:", model_worker.ModelWorker.run.__globals__.get("_cta_hook"))
'
