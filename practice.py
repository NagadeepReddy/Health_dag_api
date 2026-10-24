cd /application1/sajjna8/rt-pzaas-cta-offers-v1

sed -n '1,130p' \
artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py

sed -n '1,65p' \
artifacts/v1.168-max/cta_max/live_cta_pipeline_bridge.py
