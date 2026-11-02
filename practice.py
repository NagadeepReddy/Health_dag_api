echo "=== BPLAN PORT ==="
ss -ltnp | grep ':18768' || echo "NOT LISTENING"

echo "=== ACTIVE MAX WORKERS ==="
ps -eo pid,ppid,stat,etime,args \
  | grep -E '[b]plan|[m]axserve|[m]odel_worker|[s]pawn_main' \
  | head -35

echo "=== BPLAN HEALTH ==="
curl -sS --max-time 5 -o /dev/null \
  -w 'HTTP STATUS: %{http_code}\n' \
  http://127.0.0.1:18768/openapi.json
