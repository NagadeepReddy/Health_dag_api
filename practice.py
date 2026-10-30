echo "=== OPTIMIZED MAX HEALTH ==="
curl --noproxy '*' -sS --max-time 10 \
  -o /dev/null -w 'PORT 8766 HTTP: %{http_code}\n' \
  http://127.0.0.1:8766/health

echo "=== ORIGINAL MAX HEALTH ==="
curl --noproxy '*' -sS --max-time 10 \
  -o /dev/null -w 'PORT 8765 HTTP: %{http_code}\n' \
  http://127.0.0.1:8765/health
