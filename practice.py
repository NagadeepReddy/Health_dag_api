cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none --memory=4g \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -c '
from max.serve.pipelines import model_worker
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper

before = model_worker.load_scheduler
CTAFactoryWrapper(lambda: None)()
after = model_worker.load_scheduler

print("MAX WORKER SCHEDULER HOOK ACTIVE:", before is not after)
print("ACTUAL SCHEDULER FUNCTION:", after.__module__, after.__name__)
' 2>&1 | tail -8
