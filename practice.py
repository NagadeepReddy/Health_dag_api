cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 75s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --network=none --memory=8g --cpus=2 \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max:/workspace/artifacts/v1.168/core-artifact \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  -e OTEL_SDK_DISABLED=true \
  -e OTEL_TRACES_EXPORTER=none \
  -e OTEL_METRICS_EXPORTER=none \
  -e OTEL_LOGS_EXPORTER=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY' 2>&1 | grep -Ei 'CTA|worker|ready|error|exception|traceback|telemetry|failed'
import sys, runpy
from pipeline import pipeline as CTA
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper
from max.pipelines import PipelineConfig, PIPELINE_REGISTRY

TARGET = "/workspace/artifacts/v1.168/core-artifact"

def is_cta(config):
    return str(config.model_config.model_path) == TARGET

resolve_original = PipelineConfig.resolve
log_original = PipelineConfig.log_basic_config
registry = type(PIPELINE_REGISTRY)
factory_original = registry.retrieve_factory

def resolve(self):
    if is_cta(self):
        print("CTA CONFIG ACTIVE", flush=True)
        return
    return resolve_original(self)

def log_config(self):
    if is_cta(self):
        return
    return log_original(self)

def factory(self, config, *args, **kwargs):
    if is_cta(config):
        print("CTA REAL FACTORY SELECTED", flush=True)
        return None, CTAFactoryWrapper(CTA)
    return factory_original(self, config, *args, **kwargs)

PipelineConfig.resolve = resolve
PipelineConfig.log_basic_config = log_config
registry.retrieve_factory = factory

launcher = "/workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py"
sys.argv = [launcher, "--headless", "--devices", "cpu", "--model-path", TARGET]

runpy.run_path(launcher, run_name="__main__")
PY

echo "PODMAN EXIT CODE: ${PIPESTATUS[0]}"
