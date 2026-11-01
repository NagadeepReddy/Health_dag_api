CTA=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max

grep -RnE --include='*.py' \
'np\.save\(|fn_attn_out_weight|fn_rotary_emb_inv_freq|seq_dense_bias' \
"$CTA" 2>/dev/null | head -65
