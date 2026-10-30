curl --noproxy '*' -sS \
  --connect-timeout 3 --max-time 10 \
  -w '\nHTTP STATUS: %{http_code}\n' \
  http://127.0.0.1:8765/health
