POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== NATIVE MAX RESTART CHECK ==="

if ! "${POD[@]}" container exists cta-native-live; then
  echo "STOP: Native container not found"
else
  AUTO=$("${POD[@]}" inspect --format '{{.HostConfig.AutoRemove}}' cta-native-live)

  if [ "$AUTO" = "true" ]; then
    echo "RESTART NOT ATTEMPTED: Container uses --rm"
    echo "Original launch configuration must be preserved"
  elif [ "$AUTO" = "false" ]; then
    echo "RESTARTING EXISTING NATIVE MAX CONTAINER"
    "${POD[@]}" restart --time 30 cta-native-live
    echo "RESTART COMMAND: COMPLETED"
    echo "MAX STARTUP: VERIFY NEXT"
  else
    echo "STOP: Could not verify restart safety"
  fi
fi
