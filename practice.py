cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
grep -nE 'llama_arch|pipeline_model|default_encoding|weight|register' artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py
