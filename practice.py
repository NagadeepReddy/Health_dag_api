echo "=== ACTIVE CONTAINER OVERLAY MOUNTS ==="
findmnt -rn -t overlay -o TARGET | head -25

echo "=== RECENT RUNTIME / FILESYSTEM ERRORS ==="
journalctl -k --since "30 minutes ago" --no-pager 2>/dev/null \
  | grep -Ei 'no space left|overlay|xfs|quota|enospc|oom' \
  | tail -25 || true

echo "=== CONTAINER RUNTIME PROCESSES ==="
ps -eo pid,stat,args \
  | grep -E '[c]run|[c]onmon|[p]odman' \
  | head -20
