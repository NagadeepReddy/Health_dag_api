P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== ACTUAL HTTP SERVER ==="
ss -lntp '( sport = :18768 )'

echo "=== CONTAINER PROCESS IDENTITIES ==="
for name in $("${P[@]}" ps -a --format '{{.Names}}' | grep -i bplan); do
  echo "CONTAINER: $name"
  "${P[@]}" inspect --format 'PID={{.State.Pid}} STATUS={{.State.Status}} STARTED={{.State.StartedAt}}' "$name"
done

echo "=== SERVER PROCESS ==="
PID=$(ss -lntp '( sport = :18768 )' | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2)
if [ -n "$PID" ]; then
  ps -fp "$PID"
  tr '\0' ' ' < "/proc/$PID/cmdline"
  echo
fi
