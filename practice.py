podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
import inspect
from max.pipelines.lib import PipelineModel
for name in ("execute", "prepare_initial_token_inputs", "prepare_next_token_inputs"):
    method = getattr(PipelineModel, name)
    print(name, inspect.signature(method))
    print(inspect.getsource(method)[:1800])
'
