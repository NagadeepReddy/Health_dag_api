cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

grep -RnE '_cta_native_pipeline|_cta_adapter' \
  artifacts/v1.168-max/maxserve_cta_extension \
  --include='*.py' | head -25
