echo "=== DISTINCT BATCH-2 PROCESS STATUS ==="
ps -eo pid,ppid,stat,etime,%cpu,%mem,args |
grep -E '[r]un_distinct_batch2_live_max_inference|[t]imeout 300s podman|[c]onmon' |
head -20

echo "=== MEMORY AVAILABLE ==="
free -h

echo "=== CONTAINER STATUS ==="
timeout 10s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' |
grep -E 'NAMES|cta-max|MAX|faiss' || true

echo "=== STATUS CHECK COMPLETE ==="
