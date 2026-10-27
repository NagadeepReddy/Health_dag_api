grep -RnE 'MAXModelConfig|PipelineConfig|_resolve_weight_path|weight_path|weights_format|validate_and_resolve' \
  /application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/maxserve_cta_extension \
  --include='*.py' | head -50
