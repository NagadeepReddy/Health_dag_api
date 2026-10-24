cd /application1/sajjna8/rt-pzaas-cta-offers-v1

cat > artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py <<'PY'
"""CTA integration with MAX Serve's built-in worker queues."""

from max.serve.pipelines import TokenGeneratorPipeline


class CTANativeHTTPPipeline(TokenGeneratorPipeline):
    """Reuse MAX's EngineQueue lifecycle for structured CTA JSON."""

    def __init__(
        self,
        model_name,
        worker_monitor,
        scheduler_zmq_configs,
    ):
        super().__init__(
            model_name=model_name,
            tokenizer=None,
            worker_monitor=worker_monitor,
            scheduler_zmq_configs=scheduler_zmq_configs,
            lora_queue=None,
        )
PY

python3 -m py_compile \
  artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py \
  && echo "CTA NATIVE HTTP PIPELINE ADAPTER: SYNTAX PASS"
