echo "=== AVAILABLE MEMORY ==="
free -h

echo "=== RUNNING CONTAINER MEMORY ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  stats --no-stream cta-clean-native-batch2

echo "=== HANDOFF STAGE ==="
bash /application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/run_cta_native.sh check
