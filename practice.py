B=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

echo "=== PATH REFERENCE ==="
nl -ba "$B/bplan_max_dev/parallel_transformer_block_2layers.py" | sed -n '55,90p'

echo "=== BPLAN NORMALIZATION WEIGHTS ==="
find "$B" -name 'fn_norm1_g.npy' -o -name 'fn_norm2_g.npy' -o -name 'fn_norm1_g_layer1.npy' -o -name 'fn_norm2_g_layer1.npy'
