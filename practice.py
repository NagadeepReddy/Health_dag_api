POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

NAME=cta-batch2-trace-8766

echo "=== CONTAINER STATE ==="
"${POD[@]}" inspect --format '{{.State.Status}}' "$NAME"

echo "=== ISOLATED MAX HEALTH ==="
curl --noproxy '*' -sS --max-time 10 \
  -o /dev/null -w 'HTTP STATUS: %{http_code}\n' \
  http://127.0.0.1:8766/health

echo "=== ISOLATED MAX STARTUP LOGS ==="
"${POD[@]}" logs --tail 50 "$NAME" 2>&1

echo "=== ORIGINAL MAX HEALTH ==="
curl --noproxy '*' -sS --max-time 10 \
  -o /dev/null -w 'HTTP STATUS: %{http_code}\n' \
  http://127.0.0.1:8765/health
