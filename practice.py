PID=$(ss -H -ltnp '( sport = :8766 )' | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)

if [ -z "$PID" ]; then
  echo "STOP: Optimized server not running"
else
  Q="/proc/$PID/root/opt/venv/lib/python3.12/site-packages/max/serve/scheduler/queues.py"

  if [ -f "$Q" ]; then
    echo "=== MAX RESPONSE QUEUE IMPLEMENTATION ==="
    sed -n '125,265p' "$Q"
  else
    echo "STOP: MAX queue source unavailable"
  fi
fi
