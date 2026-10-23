cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 80s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --network=none --memory=8g --cpus=2 \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max:/workspace/artifacts/v1.168/core-artifact \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  -e OTEL_SDK_DISABLED=true \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import sys, runpy, threading, time, json, urllib.request

from pipeline import pipeline as CTA
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper
from max.pipelines import PipelineConfig, PIPELINE_REGISTRY

TARGET = "/workspace/artifacts/v1.168/core-artifact"

def is_cta(config):
    return str(config.model_config.model_path) == TARGET

old_resolve = PipelineConfig.resolve
old_log = PipelineConfig.log_basic_config
registry_class = type(PIPELINE_REGISTRY)
old_factory = registry_class.retrieve_factory

def resolve(self):
    if is_cta(self):
        return
    return old_resolve(self)

def log_config(self):
    if is_cta(self):
        return
    return old_log(self)

def factory(self, config, *args, **kwargs):
    if is_cta(config):
        print("REAL CTA FACTORY: SELECTED", flush=True)
        return None, CTAFactoryWrapper(CTA)
    return old_factory(self, config, *args, **kwargs)

PipelineConfig.resolve = resolve
PipelineConfig.log_basic_config = log_config
registry_class.retrieve_factory = factory

def check_endpoint():
    for attempt in range(50):
        try:
            with urllib.request.urlopen(
                "http://127.0.0.1:8000/openapi.json",
                timeout=2
            ) as response:
                data = json.load(response)
            print("MAX HTTP ENDPOINT: PASS", flush=True)
            for path, methods in data.get("paths", {}).items():
                print("ROUTE:", path, list(methods), flush=True)
            return
        except Exception:
            time.sleep(1)
    print("MAX HTTP ENDPOINT: NOT REACHABLE", flush=True)

threading.Thread(target=check_endpoint, daemon=True).start()

launcher = "/workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py"
sys.argv = [
    launcher, "--devices", "cpu",
    "--port", "8000", "--model-path", TARGET
]

print("STARTING MAX HTTP SERVER WITH REAL CTA", flush=True)
runpy.run_path(launcher, run_name="__main__")
PY

echo "EXIT CODE: $?"
