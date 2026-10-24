cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
from max.serve import api_server
from max.serve.pipelines import model_worker
from maxserve_cta_extension.cta_spawn_worker import install_cta_spawn_entry

install_cta_spawn_entry()

a = api_server.start_model_worker
b = model_worker.start_model_worker

print("CTA WORKER WRAPPED:", getattr(a, "_cta_wrapped", False))
print("MAX SERVER HOOK CONNECTED:", a is b)
print("RESULT:", "PASS" if getattr(a, "_cta_wrapped", False) and a is b else "FAIL")
PY
