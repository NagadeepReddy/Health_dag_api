BASE=/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension

nl -ba "$BASE/cta_native_launcher.py" | sed -n '1,110p'
