echo "=== PODMAN STORAGE ==="
podman info --format '{{.Store.GraphRoot}}' 2>&1
echo "=== ALL IMAGES ==="
podman images --format '{{.Repository}}:{{.Tag}}' 2>&1 | head -20
echo "=== ALL CONTAINERS ==="
podman ps -a --format '{{.Names}} | {{.Image}}' 2>&1 | head -20
echo "=== APPLICATION1 MOUNT ==="
findmnt /application1
