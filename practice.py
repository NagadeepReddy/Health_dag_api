DST=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

grep -RnE --include='*.py' \
'sequence_weights|fn_norm1_g' "$DST" | cut -c1-220
