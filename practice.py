cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -nE 'dump_traceback_later|faulthandler|timeout|alarm|exit=True' \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py
