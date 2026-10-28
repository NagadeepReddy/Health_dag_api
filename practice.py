cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -nE 'def predict_raw|def predict\(|dump_traceback_later|faulthandler|timeout|alarm' \
artifacts/v1.168/core-artifact/pipeline.py \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py
