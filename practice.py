cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

grep -Rnl --include='*.py' \
  -E 'MAXModelConfig|ModelBridge|weights_registry' \
  artifacts/v1.168-max/maxserve_cta_extension
