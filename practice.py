cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 60s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --network=none --memory=6g --cpus=2 --pids-limit=64 \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import sys
import runpy
from max.pipelines import PipelineConfig

original_resolve = PipelineConfig.resolve

def cta_resolve(self):
    path = str(self.model_config.model_path)
    if path == "/workspace/artifacts/v1.168/core-artifact":
        print("CTA: BYPASSED HF CONFIG VALIDATION", flush=True)
        return None
    return original_resolve(self)

PipelineConfig.resolve = cta_resolve

launcher = "/workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py"
sys.argv = [
    launcher,
    "--headless",
    "--devices", "cpu",
    "--model-path", "/workspace/artifacts/v1.168/core-artifact"
]

print("STARTING NATIVE CTA WORKER", flush=True)
runpy.run_path(launcher, run_name="__main__")
PY

echo "EXIT CODE: $?"
