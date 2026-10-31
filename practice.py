podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-native-batch2 /bin/sh -c '
for pid in 1 69 70; do
  echo "=== PID $pid ==="
  readlink /proc/$pid/cwd || continue

  for f in \
    /batch2/cta_max/grecbase_integration_weights/seq_dense_weight.npy \
    /batch2/cta_max/grecbase_integration_weights/att_pooling.rotary_emb.inv_freq.npy \
    /proc/$pid/cwd/artifacts/v1.168/core-artifact/model_0_base.pt
  do
    if test -r "$f"; then
      echo "PASS: $f"
    else
      echo "MISSING: $f"
    fi
  done
done
'
