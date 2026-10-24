cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE 'register_cta_architecture|custom.architectures|runpy|sys.argv|register_cta_routes' \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py
