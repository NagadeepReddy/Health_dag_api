cd /application1/sajjna8/rt-pzaas-cta-offers-v1

cat > artifacts/v1.168-max/maxserve_cta_extension/cta_pipeline_model.py <<'PY'
"""CTA-specific MAX PipelineModel integration.

Original DS pipeline and business logic remain unchanged.
"""

from max.pipelines.lib import PipelineModel


class CTAMaxPipelineModel(PipelineModel):
    """Native MAX model contract for CTA Offers."""

    @classmethod
    def calculate_max_seq_len(
        cls, pipeline_config, huggingface_config
    ) -> int:
        return 50

    @classmethod
    def infer_optimal_batch_size(cls, *args, **kwargs) -> int:
        return 1
PY

python3 -m py_compile \
  artifacts/v1.168-max/maxserve_cta_extension/cta_pipeline_model.py \
  && echo "CTA NATIVE MODEL CLASS: INITIAL IMPLEMENTATION CREATED"
