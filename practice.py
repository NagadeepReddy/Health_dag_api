unshare -m --propagation private sh -c '
mount --bind /application /application1 &&
timeout 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  -v /application/sajjna8/rt-pzaas-cta-offers-v1:/workspace:ro \
  -e CTA_MAX_NATIVE_BOOTSTRAP=1 \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max/maxserve_cta_extension/bootstrap \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -u -c "
import sys, inspect
from max.serve.pipelines.model_worker import ModelWorker
assert \"sitecustomize\" in sys.modules
hook = inspect.unwrap(ModelWorker.run).__globals__.get(\"load_scheduler\")
assert getattr(hook, \"_cta_hook\", False)
print(\"FRESH BOOTSTRAP: PASS\")
print(\"CTA WORKER HOOK: PASS\")
"
'
