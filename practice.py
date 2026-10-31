ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

echo "=== LAUNCHER CHECK ==="
bash "$ROOT/run_cta_native.sh" check

echo "=== CURRENT RUNTIME IMAGE ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect cta-clean-native-batch2 \
  --format 'IMAGE={{.Config.Image}}'

echo "=== PACKAGE SIZE ==="
du -sh "$ROOT"
