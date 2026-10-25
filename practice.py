podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
import inspect
from max.serve.pipelines import model_worker

print("=== NATIVE WORKER STARTUP ===")
print(inspect.getsource(model_worker.start_model_worker))
'
