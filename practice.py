cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
grep -nE 'model_path|model-name|model-path|cta_native_model|sys.argv|run_module' artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py artifacts/v1.168-max/maxserve_cta_extension/cta_native_startup_test.py
