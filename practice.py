DST=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

grep -nE -C 3 'seq_dense|grecbase_integration_weights|BPLAN_BASE_PT|model_0_base' "$DST"/*.py
