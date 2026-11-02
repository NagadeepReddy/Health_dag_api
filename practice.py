P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

for id in $("${P[@]}" ps -q); do
  info=$("${P[@]}" inspect --format \
    '{{json .Config.Env}} {{json .Config.Cmd}} {{json .Config.Entrypoint}}' "$id" 2>/dev/null)

  if [[ "$info" == *bplan* || "$info" == *v1.113* ]]; then
    echo "=== BPLAN CONTAINER: $id ==="
    "${P[@]}" logs --tail 200 "$id" 2>&1 |
      grep -Ei 'BPLAN|WORKER|QUEUE|RECEIVER|SCHEDULER|ERROR|TRACEBACK|EXCEPTION'
  fi
done
