podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-native-batch2 /bin/sh -c '
for pid in 1 69 70; do
  echo "=== PID $pid ==="
  readlink /proc/$pid/ns/mnt
  readlink -f /proc/$pid/root/batch2/cta_max/grecbase_integration_weights/seq_dense_weight.npy
done
'
