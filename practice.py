echo "=== DISK SPACE ==="
df -hP /application1 /run /var /tmp /home

echo "=== INODE AVAILABILITY ==="
df -iP /application1 /run /var /tmp /home

echo "=== PODMAN STORAGE PATHS ==="
ls -ld /application1/podman/storage /run/containers/storage 2>&1
