echo "=== PODMAN STORAGE SPACE ==="
df -hP /application1/podman/storage /run/containers/storage

echo "=== PODMAN STORAGE INODES ==="
df -iP /application1/podman/storage /run/containers/storage

echo "=== STORAGE FILESYSTEM TYPES ==="
findmnt -T /application1/podman/storage -o TARGET,FSTYPE,OPTIONS
findmnt -T /run/containers/storage -o TARGET,FSTYPE,OPTIONS
