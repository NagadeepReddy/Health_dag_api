podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
import inspect
from max.serve.pipelines.model_worker import ModelWorker

fn = inspect.unwrap(ModelWorker.run).__globals__["get_paged_manager"]
print("=== WORKER PAGED MANAGER CONTRACT ===")
print(inspect.getsource(fn))
'
