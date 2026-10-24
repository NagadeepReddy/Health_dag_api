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
    print("\n===", name, "TYPES ===")
    for key, value in inspect.get_annotations(method, eval=True).items():
        print(key, ":", value)
        if key == "return":
            try:
                print("CONSTRUCTOR:", inspect.signature(value))
                print("FIELDS:", getattr(value, "__annotations__", {}))
            except (TypeError, ValueError):
                pass

print("\nCTA MODEL TYPE CONTRACT CHECK COMPLETE")
PY
