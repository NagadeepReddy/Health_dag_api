ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

for f in grecbase_fusion_full_head_72_max.py parallel_transformer_block_2layers.py sequence_postprocess_max.py run_real_sanity_input_adapter.py; do
  echo "=== $f ==="
  grep -nE 'TensorType|seq_len|seq_length|seq_dense|page_wide|reshape|range\(50\)|\[1, 50|\[1, 20|== 50|valid_length' "$ROOT/$f" | head -35
done
