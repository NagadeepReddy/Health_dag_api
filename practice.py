cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
grep -nE 'sys.exit|exit\(|raise |except |main\(' artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py
