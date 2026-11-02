P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

CID=$("${P[@]}" ps --format '{{.ID}} {{.Command}}' |
  awk '/bplan_native_serve_dev.bplan_native_launcher/ {print $1; exit}')

if [ -z "$CID" ]; then
  echo "BPLAN CONTAINER NOT FOUND"
else
  echo "BPLAN CONTAINER: $CID"
  echo "=== WORKER / QUEUE LOGS ==="
  "${P[@]}" logs --tail 200 "$CID" 2>&1 |
    grep -Ei 'BPLAN|WORKER|QUEUE|RECEIVER|SCHEDULER|ERROR|TRACEBACK|EXCEPTION|18768'
fi
