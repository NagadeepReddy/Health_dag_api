cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -RnE '^class CTA\b|^class .*PipelineModel|def (execute|prepare_initial_token_inputs|prepare_next_token_inputs|calculate_max_seq_len)\(' \
  artifacts/v1.168-max/cta_max/ \
  artifacts/v1.168-max/maxserve_cta_extension/ \
  --include='*.py' | head -40
