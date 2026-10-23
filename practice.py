cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 90s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --network=none --memory=8g --cpus=2 \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max:/workspace/artifacts/v1.168/core-artifact \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import sys, runpy
from pipeline import pipeline as CTA
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper
from max.pipelines import PipelineConfig, PIPELINE_REGISTRY

TARGET = "/workspace/artifacts/v1.168/core-artifact"

def is_cta(config):
    return str(config.model_config.model_path) == TARGET

original_resolve = PipelineConfig.resolve
original_log = PipelineConfig.log_basic_config
registry_class = type(PIPELINE_REGISTRY)
original_factory = registry_class.retrieve_factory

def resolve(self):
    if is_cta(self):
        print("CTA CONFIG: PASS", flush=True)
        return
    return original_resolve(self)

def log_basic_config(self):
    if is_cta(self):
        print("CTA LOGGING: PASS", flush=True)
        return
    return original_log(self)

def retrieve_factory(self, config, *args, **kwargs):
    if is_cta(config):
        print("CTA REAL FACTORY: SELECTED", flush=True)
        return None, CTAFactoryWrapper(CTA)
    return original_factory(self, config, *args, **kwargs)

PipelineConfig.resolve = resolve
PipelineConfig.log_basic_config = log_basic_config
registry_class.retrieve_factory = retrieve_factory

launcher = "/workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py"
sys.argv = [
    launcher, "--headless",
    "--devices", "cpu",
    "--model-path", TARGET
]

print("STARTING REAL CTA NATIVE WORKER", flush=True)
runpy.run_path(launcher, run_name="__main__")
PY

echo "EXIT CODE: $?"
