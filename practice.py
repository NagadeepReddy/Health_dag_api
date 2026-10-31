podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-native-batch2 /bin/sh -c '
for f in \
/batch2/cta_max/grecbase_integration_weights/att_pooling.rotary_emb_inv_freq.npy \
/batch2/cta_max/artifacts/v1.168/core-artifact/model_0_base.pt \
/workspace/artifacts/v1.168/core-artifact/model_0_base.pt
do
  if test -f "$f"; then echo "FOUND: $f"
  else echo "MISSING: $f"; fi
done'
