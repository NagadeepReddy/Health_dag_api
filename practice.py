cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none --memory=4g \
-v "$PWD:/workspace:Z" -w /workspace \
-e PYTHONPATH=/workspace/artifacts/v1.168-max \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
import inspect
from types import SimpleNamespace
from max.serve.pipelines.model_worker import ModelWorker
from maxserve_cta_extension.cta_worker_registration import install_cta_scheduler_hook

install_cta_scheduler_hook()
select = inspect.unwrap(ModelWorker.run).__globals__["load_scheduler"]

pipeline = SimpleNamespace(
    _cta_native_pipeline=True,
    _cta_adapter=object()
)

try:
    scheduler = select(pipeline, None, None, None)
    print("CTA SCHEDULER CREATED:", type(scheduler).__name__)
except Exception as e:
    print("CTA SCHEDULER ERROR:", type(e).__name__, str(e))
    raise
'
