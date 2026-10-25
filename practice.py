podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
import inspect
from max.pipelines.lib.model_config import MAXModelConfig

print("=== MAX MODEL RESOLVE ===")
print(inspect.getsource(MAXModelConfig.resolve))
'
