cd /application1/sajjna8/rt-pzaas-cta-offers-v1

find artifacts/v1.168-max \
  \( -name 'fn_rotary_emb_inv_freq.npy' \
  -o -name 'att_pooling.rotary_emb.inv_freq.npy' \) \
  -print

sed -n '55,95p' \
  artifacts/v1.168-max/cta_max/run_real_sanity_input_adapter.py
