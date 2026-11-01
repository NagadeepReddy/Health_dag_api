echo "=== ML IMAGES ==="
podman images --format '{{.Repository}}:{{.Tag}}' | grep -Ei 'max|modular|cta|torch|faiss' || true
echo "=== ML CONTAINERS ==="
podman ps -a --format '{{.Names}} | {{.Image}} | {{.Status}}' | grep -Ei 'max|cta|torch|faiss' || true
