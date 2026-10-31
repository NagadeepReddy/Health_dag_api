PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== WEIGHT TIMESTAMPS ==="
$PODMAN exec cta-clean-native-batch2 /bin/sh -c '
date -u
stat -c "%y %n" \
 /batch2/cta_max/grecbase_integration_weights \
 /batch2/cta_max/sequence_weights/seq_dense_weight.npy
'

echo "=== LAST WEIGHT ERRORS ==="
$PODMAN logs --timestamps --tail 150 \
 cta-clean-native-batch2 2>&1 |
 grep -E 'FileNotFoundError|CTA PREDICT EXCEPTION' |
 tail -8
