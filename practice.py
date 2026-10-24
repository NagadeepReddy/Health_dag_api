cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE 'BASE[[:space:]]*=|freq_dir[[:space:]]*=|No exported 256-d|No expected 256-d' \
  artifacts/v1.168-max/cta_max/run_real_sanity_input_adapter.py \
  artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py \
  artifacts/v1.168-max/cta_max/run_live_max_inference.py
