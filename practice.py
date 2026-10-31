podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-native-batch2 /bin/sh -c '
echo "=== WEIGHT DIRECTORY ==="
ls -lah /batch2/cta_max/grecbase_integration_weights/
echo "=== REQUIRED WEIGHT REFERENCES ==="
sed -n "30,70p" /batch2/cta_max/grecbase_fusion_full_head_72_max.py
'
