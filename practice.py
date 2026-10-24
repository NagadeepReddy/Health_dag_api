cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c '
import inspect
from maxserve_cta_extension.cta_http_pipeline import CTANativeHTTPPipeline

print("CTA ADAPTER:", inspect.signature(CTANativeHTTPPipeline))
try:
    inspect.signature(CTANativeHTTPPipeline).bind(
        model_name="cta",
        tokenizer=None,
        lora_queue=None,
        scheduler_zmq_configs=None,
    )
    print("MAX LIFECYCLE ARGUMENTS: PASS")
except TypeError as e:
    print("MAX LIFECYCLE ARGUMENTS: MISMATCH")
    print(e)
'
