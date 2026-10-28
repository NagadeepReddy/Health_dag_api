echo "=== CONTAINER STORAGE FILESYSTEMS ==="
df -hP / /dev/shm /application1/podman/storage /run/containers/storage

echo "=== CONTAINER STORAGE INODES ==="
df -iP / /dev/shm /application1/podman/storage /run/containers/storage

echo "=== PODMAN STORAGE MOUNTS ==="
findmnt -T /application1/podman/storage
findmnt -T /run/containers/storage
