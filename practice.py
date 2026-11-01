DST=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

grep -nE 'model_0_base|v1\.168|cta_max|CTA_|WDIR|2048|10438|10819|10727|72 inputs' \
  "$DST/grecbase_fusion_full_head_72_max.py" \
  "$DST/main_context_max.py" \
  "$DST/grecbase_aux_branches_max.py" \
  "$DST/sequence_transformer_max.py" \
  "$DST/grecbase_get_path_max.py" | head -100
