podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-batch2-http-20261030 \
  /bin/sh -c '
echo "=== COMPLETE LATEST WORKER ERROR ==="
tail -n 85 /tmp/cta_clean_http_retry.log
'
