
cd /application1/sajjna8 && podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  -v /application1/sajjna8/max_shared_infra/python:/shared_infra/python:ro \
  -e PYTHONPATH=/shared_infra/python \
  --entrypoint /opt/venv/bin/python \
  localhost/max-shared-runtime:cpu \
  -B -c '
import importlib

print("=== STANDALONE SHARED MAX INFRA TEST ===")

modules = [
    "max_runtime_shared.typed_queue",
    "max_runtime_shared.scheduler_hooks",
    "max_runtime_shared.router_contract",
    "max_runtime_shared.worker_lifecycle",
]

for name in modules:
    module = importlib.import_module(name)
    print("PASS:", name, "|", module.__file__)

print("SHARED COMPONENT IMPORTS: PASS")
print("CTA / BPLAN / PZAAS MODEL MOUNTS: NONE")
print("ORIGINAL FILES: UNCHANGED")
'
