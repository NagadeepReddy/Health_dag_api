cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -RIn -C 5 \
  --include='*.py' \
  -E 'real_sanity_model_in\.pt|torch\.save\(.*model_in|save\(model_in|build_real_inputs\(model_in|def attach_max' \
  artifacts/v1.168-max/cta_max \
  artifacts/v1.168-max/maxserve_cta_extension \
  2>/dev/null | head -160
