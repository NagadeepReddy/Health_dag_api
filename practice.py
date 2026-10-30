podman --root /application1/podman/storage \
--runroot /run/containers/storage \
exec 0c95d4a8f887 sh -c '
echo "=== BATCH-2 CONTAINER MEMORY ==="
cat /sys/fs/cgroup/memory.max
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.events
echo "=== MEMORY AVAILABLE ==="
free -h
echo "=== REQUIRED MOUNTS ==="
ls -ld /batch2 /workspace
echo "=== AVAILABLE STORAGE ==="
df -h /tmp /workspace
'
