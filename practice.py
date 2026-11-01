DST=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

grep -n -C 3 -E 'fn_rotary_emb_inv_freq|out_norm1_g|out_norm2_g|rotary_emb|att_pooling.norm|moe_norm' "$DST"/*.py | head -110
