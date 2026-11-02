P="podman --root /application1/podman/storage --runroot /run/containers/storage"

ID=$($P ps --no-trunc --format '{{.ID}} {{.Command}}' | awk '/bplan_native_launcher/ {print $1; exit}')

if [ -z "$ID" ]; then
  echo "BPLAN CONTAINER NOT RUNNING"
else
  echo "BPLAN CONTAINER: $ID"
  $P logs --tail 400 "$ID" 2>&1 | grep -Ei \
    'BPLAN|scheduler|queue|factory|response|socket|predict|POST|traceback|error|exception' | tail -100
fi
