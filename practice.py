DST=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

grep -nE 'WDIR[[:space:]]*=|grecbase_integration_weights|from .* import WDIR' "$DST"/*.py || true
