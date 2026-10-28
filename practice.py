echo "=== OCI RUNTIME STORAGE CHECK ==="
df -hP /var /var/lib/containers/storage /tmp /dev/shm
df -iP /var /var/lib/containers/storage
