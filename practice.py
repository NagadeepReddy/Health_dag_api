P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== PORT 18768 OWNER ==="
ss -lntp | grep ':18768' || true

echo "=== ALL BPLAN CONTAINERS ==="
"${P[@]}" ps -a --format '{{.Names}} | {{.Status}}' | grep -i bplan || true

echo "=== BPLAN INFERENCE LOGS ==="
while IFS= read -r name; do
  echo "=== $name ==="
  "${P[@]}" logs --tail 350 "$name" 2>&1 |
    grep -Ei 'BPLAN|POST /bplan|MAX EXECUTION|RESPONSE|SCHEDULER|WORKER|Traceback|ERROR|exception|timed out' |
    tail -60
done < <("${P[@]}" ps -a --format '{{.Names}}' | grep -i bplan)
