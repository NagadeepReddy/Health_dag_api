cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -nE -C 5 \
'InferenceSession|session[[:space:]]*=|session\.load|cache|compile|device|_max_model' \
artifacts/v1.168-max/cta_max/run_live_max_inference.py
