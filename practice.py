cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

grep -RnE 'SupportedEncoding|q4_k|float32|weights|MAXModelConfig' \
  artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py \
  artifacts/v1.168-max/maxserve_cta_extension/cta_pipeline_model.py \
  artifacts/v1.168-max/cta_native_model/config.json
