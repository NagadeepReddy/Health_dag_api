echo "=== NATIVE CONTAINER EXIT EVENTS ==="

podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  events --stream=false \
  --since 2026-10-28T19:00:00Z \
  --until 2026-10-28T20:00:00Z \
  --filter container=cta_native_corrected_1028 \
  2>&1 | grep -Ei 'oom|kill|die|exit|stop|error|remove'

echo "=== CGROUP MEMORY EVENTS ==="
for f in /sys/fs/cgroup/memory.events \
         /sys/fs/cgroup/memory.swap.events; do
  if [ -r "$f" ]; then
    echo "$f"
    cat "$f"
  fi
done
