cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

echo "=== KERNEL OOM / PROCESS KILL EVENTS ==="
journalctl -k \
  --since "2026-10-28 18:45:00 UTC" \
  --until "2026-10-28 20:00:00 UTC" \
  --no-pager 2>&1 |
grep -Ei 'oom|out of memory|killed process|memory cgroup|segfault|podman|conmon|crun' |
tail -40

echo "=== REAL E2E LAST EVENTS ==="
tail -35 /application1/cta_native_corrected_1028.log

echo "=== CURRENT MEMORY ==="
free -h
