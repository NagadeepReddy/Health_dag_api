cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 35s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=4g --pids-limit=32 \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  f30453065dac \
  -u -c '
import inspect
from types import SimpleNamespace
from max.serve.pipelines.model_worker import ModelWorker
from maxserve_cta_extension import cta_worker_registration as reg

reg.install_cta_scheduler_hook()

load_scheduler = inspect.unwrap(ModelWorker.run).__globals__["load_scheduler"]

reg.create_cta_scheduler = lambda *args, **kwargs: "CTA_SELECTED"

pipeline = SimpleNamespace(
    _cta_native_pipeline=True,
    cta_adapter=object()
)

queues = SimpleNamespace(
    model_worker_queues=lambda: (None, None, None, None)
)

result = load_scheduler(pipeline, None, None, queues)

assert result == "CTA_SELECTED", result
print("REAL MAX CTA SCHEDULER SELECTION: PASS", flush=True)
'

echo "EXIT CODE: $?"
