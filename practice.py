echo "=== NATIVE MAX HEALTH ==="
curl --noproxy '*' -sS --max-time 10 \
  -w '\nHTTP STATUS: %{http_code}\n' \
  http://127.0.0.1:8765/health

echo "=== CTA ROUTE ==="
curl --noproxy '*' -sS --max-time 10 \
  -X POST \
  -w '\nHTTP STATUS: %{http_code}\n' \
  http://127.0.0.1:8765/v2/cta/probe
