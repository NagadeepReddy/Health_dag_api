podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-native-batch2 /bin/sh -c '
echo "=== SERVER PROCESS ==="
tr "\000" " " </proc/1/cmdline
echo
echo "=== SERVER ROOT WEIGHT ACCESS ==="
ls -lL /proc/1/root/batch2/cta_max/grecbase_integration_weights/seq_dense_weight.npy
echo "=== SERVER WORKING DIRECTORY ==="
readlink /proc/1/cwd
'
