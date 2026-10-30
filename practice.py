echo "=== MAX SERVER HEALTH ==="
curl --noproxy '*' -sS \
  --connect-timeout 3 --max-time 5 \
  -o /dev/null \
  -w 'HTTP STATUS: %{http_code}\n' \
  http://127.0.0.1:8765/health

echo "=== MEMORY ==="
free -h

echo "=== MAX PROCESSES ==="
ps -eo pid,etime,%cpu,%mem,rss,stat,comm \
  --sort=-rss | head -15
