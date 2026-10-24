cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -R -nE 'PIPELINE_REGISTRY|SupportedArchitecture|BertModel|register_architecture' \
  artifacts/v1.168-max/maxserve_cta_extension/ || true
