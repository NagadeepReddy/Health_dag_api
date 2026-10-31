podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-batch2-http-20261030 \
  /bin/sh -c '
echo "=== MOJO CACHE IMPLEMENTATION ==="
sed -n "115,180p" /opt/venv/lib/python3.12/site-packages/mojo/importer.py

echo "=== EXISTING CACHE LOCATION ==="
ls -ld /opt/venv/lib/python3.12/site-packages/max/_core_mojo \
  /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__ 2>&1

echo "READ-ONLY CHECK COMPLETE"
'
