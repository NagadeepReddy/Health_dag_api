DST=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

for f in att_pooling_max.py main_context_max.py sibling_context_max.py grecbase_get_path_max.py grecbase_aux_branches_max.py; do
  echo "=== $f ==="
  grep -nE 'WDIR|BASE|export_dir|np.load|torch.load|\.npy|v1\.168' "$DST/$f" | head -25
done
