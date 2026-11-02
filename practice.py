W=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_helper_weights_stage/grecbase_integration_weights

for f in att_pooling.norm1_g.npy fn_norm1_g.npy fn_norm1_g_layer1.npy fn_norm2_g.npy; do
  if test -s "$W/$f"; then
    echo "PASS: $f"
  else
    echo "MISSING: $f"
  fi
done
