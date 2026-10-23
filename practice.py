cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 40s podman \
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

install_cta_spawn_entry()

assert getattr(
    model_worker.start_model_worker, "_cta_wrapped", False
), "Model-worker hook missing"

assert getattr(
    workers.start_model_worker, "_cta_wrapped", False
), "Headless hook missing"

assert (
    workers.start_model_worker
    is model_worker.start_model_worker
), "Worker references differ"

print("MODEL WORKER HOOK: PASS", flush=True)
print("HEADLESS WORKER HOOK: PASS", flush=True)
print("WORKER REFERENCES: MATCH", flush=True)
PY

echo "EXIT CODE: $?"
