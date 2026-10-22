cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=8g --pids-limit=32 \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  f30453065dac \
  -u -c '
from max.serve.pipelines import model_worker, api_server
from maxserve_cta_extension.cta_spawn_worker import install_cta_spawn_entry

install_cta_spawn_entry()
assert api_server.start_model_worker is model_worker.start_model_worker
print("MAX API TO CTA WORKER WIRING: PASS", flush=True)
'
echo "EXIT CODE: $?"
