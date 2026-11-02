P="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== RUNNING CONTAINERS ==="
$P ps --format '{{.ID}} {{.Image}} {{.Command}}'

echo "=== MAX / BPLAN WORKER PROCESSES ==="
ps -eo pid,ppid,etime,args --forest | grep -E 'bplan|model_worker|multiprocessing.spawn|18768' | grep -v grep

echo "=== BPLAN CONTAINER PROCESSES ==="
for id in $($P ps --format '{{.ID}}'); do
  echo "CONTAINER: $id"
  $P top "$id" pid,ppid,args 2>&1 | grep -E 'PID|bplan|python|spawn'
done
