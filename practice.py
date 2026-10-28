cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
nl -ba artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py \
| sed -n '55,155p'
