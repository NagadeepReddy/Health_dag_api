
cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -nE -A 5 -B 5 \
'run_module|__main__|sys.argv|install_cta|register_cta|start_workers' \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py
