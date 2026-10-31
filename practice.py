PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
NAME="cta-clean-batch2-http-20261030"

STATUS=$($PODMAN inspect "$NAME" --format '{{.State.Status}}') || exit 1
echo "CONTAINER: $STATUS"

if [ "$STATUS" = "running" ]; then
  $PODMAN exec "$NAME" /bin/sh -c '
    echo "=== WORKER STATUS / ERRORS ==="
    grep -Ei "error|failed|timeout|worker died|worker loop|ready|listening|exitcode|shutting down" \
      /tmp/cta_clean_http_retry.log | tail -n 22

    echo "=== FINAL LOG ==="
    tail -n 12 /tmp/cta_clean_http_retry.log
  '
else
  echo "Clean test container stopped; no restart performed."
fi
