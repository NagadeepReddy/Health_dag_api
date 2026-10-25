podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
import inspect
from max.serve.pipelines.model_worker import ModelWorker

print("=== SPAWNED WORKER ENTRY ===")
print(inspect.getsource(ModelWorker.__call__))
'
