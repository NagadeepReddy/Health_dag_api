cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && {
  echo "=== RECENT MAX CONTAINER EVENTS ==="
  timeout 15s podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    events --since 2h --stream=false \
    --filter type=container --format '{{json .}}' \
    2>&1 | grep -Ei 'cta-max-faiss|oom|died|die|exit|kill' | tail -25 || true

  echo "=== KERNEL OOM / PROCESS KILL EVENTS ==="
  journalctl -k --since "2 hours ago" --no-pager 2>/dev/null |
    grep -Ei 'out of memory|oom-kill|killed process|memory cgroup' |
    tail -15 || true

  echo "DIAGNOSTIC COMPLETE"
}
