cd /application1/sajjna8/rt-pzaas-v1.0 && \
mkdir -p artifacts/v1.472-max/{pzaas_max,maxserve_pzaas_extension} && \
find /application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max \
-type f \( \
-name 'cta_native_launcher.py' -o \
-name 'cta_router.py' -o \
-name 'cta_native_scheduler.py' -o \
-name 'cta_worker_adapter.py' -o \
-name 'grecbase_fusion_full_head_72_max.py' \
\) -print
