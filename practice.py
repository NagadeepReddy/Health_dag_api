podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-native-batch2 /bin/sh -c '
for f in \
  /batch2/cta_max/sequence_weights/seq_dense_weight.npy \
  /batch2/cta_max/grecbase_integration_weights/seq_dense_weight.npy
do
  if test -f "$f"; then
    echo "FOUND: $f"
  else
    echo "MISSING: $f"
  fi
done
ls -ld /batch2/cta_max/*weights* 2>&1
'
