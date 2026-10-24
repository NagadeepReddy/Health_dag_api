cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.pipelines.lib import PipelineModel

for name in ("prepare_initial_token_inputs", "execute"):
    method = getattr(PipelineModel, name)
    print(f"\n=== {name} ===", flush=True)
    print(inspect.getsource(method), flush=True)

print("\nCTA NATIVE MODEL INTERFACE REVIEW COMPLETE", flush=True)
PY
