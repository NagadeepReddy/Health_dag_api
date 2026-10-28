cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
nl -ba artifacts/v1.168-max/cta_max/run_live_max_inference.py \
| sed -n '74,174p'
