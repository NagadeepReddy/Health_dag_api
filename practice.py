cd /application1/sajjna8/rt-pzaas-cta-offers-v1

cat > artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py <<'PY'
"""Temporary MAX registry compatibility bridge for CTA."""
from dataclasses import replace

def register_cta_architecture():
    from max.pipelines.architectures.llama3.arch import llama_arch
    from max.pipelines.lib import PIPELINE_REGISTRY

    # Registration metadata only. Actual CTA execution must
    # use CTAFactoryWrapper, not the Llama pipeline.
    cta_arch = replace(llama_arch, name="BertModel")
    PIPELINE_REGISTRY.register(cta_arch, allow_override=True)
    print("CTA REGISTRY BRIDGE INSTALLED", flush=True)
PY

python3 -m py_compile \
  artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py \
  && echo "CTA REGISTRATION FILE — Syntax PASS"
