timeout -k 5s 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --memory=2g \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c '
f=$(grep -Rl --include="*.py" "^class EngineQueue" /opt/venv/lib/python3.12/site-packages/max/serve | head -1)
if [ -n "$f" ]; then
  echo "=== ENGINE QUEUE: $f ==="
  sed -n "/^class EngineQueue/,/^class /p" "$f" | head -180
else
  echo "EngineQueue class not found"
fi
'
