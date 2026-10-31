podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-native-batch2 /bin/sh -c '
echo "=== MODEL WEIGHT LOADS ==="
grep -n -C 2 "np.load" \
  /batch2/cta_max/grecbase_fusion_full_head_72_max.py
'
