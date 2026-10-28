echo "=== REMAINING TEST PROCESSES ==="
ps -eo pid,ppid,stat,etime,rss,args \
  | grep -E '[p]odman.*cta-max-faiss|[t]imeout 25s podman' \
  | head -15

echo "=== RECENT MEMORY KILLS ==="
journalctl -k --since "15 minutes ago" --no-pager 2>/dev/null \
  | grep -Ei 'oom|out of memory|killed process|memory cgroup' \
  | tail -15 || true

echo "=== AVAILABLE RAM ==="
free -h
