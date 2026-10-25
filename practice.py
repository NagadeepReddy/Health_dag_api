P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P exec -i cta-native-live /opt/venv/bin/python - <<'PY'
import inspect
from max.serve.api_server import TokenGeneratorPipeline

for cls in TokenGeneratorPipeline.__mro__:
    for name, method in cls.__dict__.items():
        if callable(method) and any(
            x in name.lower()
            for x in ("background", "startup", "response_worker")
        ):
            print(f"\n=== {cls.__name__}.{name} ===")
            try:
                src = inspect.getsource(method)
                print("\n".join(src.splitlines()[:45]))
            except (OSError, TypeError):
                print("Source unavailable")
PY
