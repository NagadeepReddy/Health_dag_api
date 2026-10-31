podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-batch2-http-20261030 \
  /bin/sh -c '
echo "=== WORKER ERROR ROOT CAUSE ==="
grep -nE "ModuleNotFoundError:|ImportError:|RuntimeError:|AttributeError:|TypeError:|ValueError:|AssertionError:|Error:" /tmp/cta_clean_http_retry.log | tail -n 15
echo "=== FINAL LOG LINES ==="
tail -n 8 /tmp/cta_clean_http_retry.log
'
