
POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-trace-8766-10g

echo "=== ISOLATED CONTAINER ==="
"${POD[@]}" inspect "$NAME" --format 'State={{.State.Status}} OOM={{.State.OOMKilled}} PID={{.State.Pid}} MemoryLimit={{.HostConfig.Memory}}'

echo "=== PORT MAPPING ==="
"${POD[@]}" port "$NAME"

echo "=== PORT 8766 LISTENER ==="
ss -ltnp '( sport = :8766 )'

echo "=== CURRENT RESOURCE USAGE ==="
timeout 15 "${POD[@]}" stats --no-stream "$NAME"

echo "=== ISOLATED STARTUP LOGS ==="
"${POD[@]}" logs --tail 100 "$NAME" 2>&1 | tail -55

echo "=== NO FILES MODIFIED ==="
