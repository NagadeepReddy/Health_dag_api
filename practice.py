POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

STATUS=$("${POD[@]}" inspect -f '{{.State.Status}}' cta-native-live 2>/dev/null) || STATUS="not-found"

if [ "$STATUS" = "exited" ]; then
  "${POD[@]}" rm cta-native-live
  echo "OLD STOPPED CONTAINER: REMOVED"
else
  echo "NO REMOVAL: STATUS=$STATUS"
fi
