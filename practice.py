cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -RnE 'class .*PipelineModel|def (prepare_next_token_inputs|prepare_initial_token_inputs|execute|calculate_max_seq_len)\(' \
  artifacts/v1.168-max/maxserve_cta_extension/ \
  --include='*.py'
