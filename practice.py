echo "=== CONTAINER RUNTIME PROCESSES ==="
ps -eo pid,ppid,stat,wchan:25,comm,args \
  | grep -E '[c]run|[c]onmon|[p]odman|[f]use-overlayfs' \
  | head -25

echo "=== OVERLAY MOUNT COUNT ==="
findmnt -rn -t overlay | wc -l

echo "=== RECENT CONTAINER ERRORS ==="
journalctl -k --since "45 minutes ago" --no-pager 2>/dev/null \
  | grep -Ei 'overlay|enospc|no space|blocked for|I/O error|oom|killed process' \
  | tail -25 || true
