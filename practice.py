echo "=== MEMORY / OOM CHECK ==="
dmesg -T 2>&1 | grep -Ei 'out of memory|oom.kill|killed process' | tail -8

echo "=== LAST FAILURE DETAILS ==="
grep -v 'CTA WORKER RESPONSE IDS: \[\]' \
  /tmp/cta_extended_e2e.log | tail -35

echo "=== AVAILABLE MEMORY ==="
free -h
