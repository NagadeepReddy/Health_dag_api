podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-native-batch2 /bin/sh -c '
echo "=== RUNNING WORKERS ==="
ps -o pid,lstart,args -p 1,69,70

echo "=== CURRENT WEIGHT DIRECTORY ==="
stat -c "%F | %y | %n" \
  /batch2/cta_max/grecbase_integration_weights \
  /batch2/cta_max/grecbase_integration_weights/seq_dense_weight.npy
'
