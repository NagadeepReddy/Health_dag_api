cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -RnE 'class .*PipelineModel|pipeline_model[[:space:]]*=|def (execute|load_model|load_weights)\(' \
  artifacts/v1.168-max/cta_native_model \
  artifacts/v1.168-max/maxserve_cta_extension \
  || echo "NO CTA PIPELINEMODEL FOUND — native implementation required"
