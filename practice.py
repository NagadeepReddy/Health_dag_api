cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 35s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --network=none --memory=4g \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
from max.entrypoints import workers
from max.serve.pipelines import model_worker
from maxserve_cta_extension.cta_spawn_worker import install_cta_spawn_entry

original = workers.start_model_worker

install_cta_spawn_entry()

print(
    "MODEL WORKER HOOK:",
    getattr(model_worker.start_model_worker, "_cta_wrapped", False),
    flush=True
)

print(
    "HEADLESS WORKER HOOK:",
    getattr(workers.start_model_worker, "_cta_wrapped", False),
    flush=True
)

print(
    "HEADLESS FUNCTION UPDATED:",
    workers.start_model_worker is not original,
    flush=True
)
PY
