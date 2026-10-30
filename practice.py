echo "=== OPTIMIZED MAX DIAGNOSIS ==="

PID=$(ss -H -ltnp '( sport = :8766 )' | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)

if [ -n "$PID" ]; then
  echo "SERVER PID: $PID"

  CID=$(sed -nE 's/.*libpod-([0-9a-f]{64})\.scope.*/\1/p' "/proc/$PID/cgroup" | head -1)

  if [ -n "$CID" ]; then
    echo "=== OPTIMIZED CONTAINER LOGS ==="
    podman --root /application1/podman/storage \
      --runroot /run/containers/storage \
      logs --tail 80 "$CID" 2>&1
  else
    echo "Container identity unavailable"
  fi
else
  echo "Optimized server not listening"
fi

echo "=== AVAILABLE MEMORY ==="
free -h
