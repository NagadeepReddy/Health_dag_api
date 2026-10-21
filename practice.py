unshare -m --propagation private sh -c '
mount --bind /application /application1 || exit
timeout -k 5s 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=1g --memory-swap=1g --pids-limit=64 \
  -v /application/sajjna8/rt-pzaas-cta-offers-v1:/workspace:ro \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max/maxserve_cta_extension \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -u -c "
import pickle
from max.serve.pipelines.model_worker import ModelWorker
from cta_spawn_worker import install_cta_spawn_entry
install_cta_spawn_entry()
assert pickle.loads(pickle.dumps(ModelWorker._call)) is ModelWorker._call
print(\"REAL MAX WORKER REGISTRATION: PASS\", flush=True)
"
'
