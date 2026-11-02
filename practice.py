P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== BPLAN CONTAINERS ==="
"${P[@]}" ps -a --format '{{.Names}} | {{.Status}}' | grep -i bplan

echo "=== BPLAN DEBUG LOGS ==="
"${P[@]}" logs --tail 150 bplan-debug 2>&1
