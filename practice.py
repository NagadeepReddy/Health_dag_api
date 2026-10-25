cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -nE 'register|_cta_adapter|cta_native_pipeline|CTAWorkerAdapter|select_scheduler' \
artifacts/v1.168-max/maxserve_cta_extension/{cta_worker_registration,cta_spawn_worker,cta_native_launcher,cta_worker_adapter}.py
