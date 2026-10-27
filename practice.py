cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
grep -nE 'model_path|model_name|model_config|cta_native_model|weights|encoding' artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py
