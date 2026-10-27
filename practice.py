cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
tar -czf /application1/cta_max_extension_pre_weight_fix_20261027.tar.gz \
  -C artifacts/v1.168-max maxserve_cta_extension &&
tar -tzf /application1/cta_max_extension_pre_weight_fix_20261027.tar.gz | tail -5
